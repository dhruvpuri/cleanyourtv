package com.gathin.tvhome;

import android.os.SystemClock;

/**
 * State of the sleep timer behind the sleep pill: the chosen length and when it ends. The countdown itself
 * runs in {@link HomeKeyService}, the one component that keeps running while another app is on screen, so
 * the timer survives leaving Home. The pill only shows this and cycles it.
 *
 * Everything here runs on the main thread (clicks, the service's handler, service lifecycle), so no locking.
 */
final class SleepTimer {
    /** The lengths one press of the pill steps through, after Off. */
    static final int[] STEPS_MINUTES = {15, 30, 60, 90};
    /** How long before the end the "going to sleep" toast shows. */
    static final long WARNING_MS = 60_000L;

    private static HomeKeyService service;
    /** The step in minutes that is running, 0 for none. */
    private static int minutes;
    /** When the timer ends, on the {@link SystemClock#uptimeMillis} clock the service's handler also uses. */
    private static long endsAt;

    private SleepTimer() {
    }

    static void attach(HomeKeyService connected) {
        service = connected;
    }

    /** The service went away, taking its countdown with it: a timer that can no longer fire must not keep showing. */
    static void detach(HomeKeyService gone) {
        if (service != gone) return;
        service = null;
        finish();
    }

    static boolean running() {
        return endsAt != 0;
    }

    /** Minutes left, rounded up so a running timer never reads 0. */
    static int minutesLeft() {
        if (!running()) return 0;
        long left = endsAt - SystemClock.uptimeMillis();
        return (int) Math.max(1, (left + 59_999L) / 60_000L);
    }

    /**
     * Off, 15, 30, 60, 90, then Off again. Returns false, and starts nothing, when no HomeKeyService is
     * connected to count down (it is an opt-in accessibility service).
     */
    static boolean cycle() {
        int next = nextStep(minutes);
        if (next == 0) {
            if (service != null) service.cancelSleep();
            finish();
            return true;
        }
        if (service == null) return false;
        minutes = next;
        endsAt = SystemClock.uptimeMillis() + next * 60_000L;
        service.armSleep(endsAt);
        return true;
    }

    /** The timer has ended or was switched off. */
    static void finish() {
        minutes = 0;
        endsAt = 0;
    }

    /** The step after {@code current} minutes: the first for Off, 0 (Off) after the last. */
    static int nextStep(int current) {
        if (current == 0) return STEPS_MINUTES[0];
        for (int i = 0; i < STEPS_MINUTES.length - 1; i++) {
            if (STEPS_MINUTES[i] == current) return STEPS_MINUTES[i + 1];
        }
        return 0;
    }
}
