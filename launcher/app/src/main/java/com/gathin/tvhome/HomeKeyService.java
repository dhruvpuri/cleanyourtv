package com.gathin.tvhome;

import android.accessibilityservice.AccessibilityService;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import android.widget.Toast;

import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Sends the remote's Home button to this launcher on remotes that emit KEYCODE_ALL_APPS for Home
 * (Xiaomi sticks and boxes). Android TV 9 routes that key only to the system-image launcher, so once
 * the stock launcher is disabled the button does nothing. A theme's {@code key_shortcuts} also turns
 * remote buttons into app launchers. Every other key passes through untouched.
 *
 * With stock_home_redirect set, it also sends the stock launcher's home screen back here, for firmware that turns
 * that launcher on again after it was disabled (XGIMI's xrmservice does, on its own remote keys).
 *
 * It also runs the sleep pill's countdown ({@link SleepTimer}): an accessibility service keeps running while
 * another app is on screen, and its lock-screen action is what puts the TV to sleep.
 *
 * Enable over adb:
 *   settings put secure enabled_accessibility_services com.gathin.tvhome/.HomeKeyService
 *   settings put secure accessibility_enabled 1
 */
public class HomeKeyService extends AccessibilityService {

    /** Remote buttons that should open Settings (config.xml or a theme: settings_key_scancodes and settings_key_keycodes). */
    private int[] settingsScancodes = new int[0];
    private int[] settingsKeycodes = new int[0];
    private boolean settingsPanel;
    /** Remote keycode to the package it launches (theme key_shortcuts). */
    private Map<Integer, String> keyShortcuts = Collections.emptyMap();
    /** The stock launcher's HOME activities (stock_home_redirect), disabled ones included. */
    private final Set<String> stockHome = new HashSet<>();

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable sleepWarning = () -> Toast.makeText(this, R.string.sleep_warning, Toast.LENGTH_SHORT).show();
    private final Runnable sleepNow = this::sleepNow;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        // Both lists and the panel choice can come from a theme; theme.sh restarts this service.
        Config config = Config.load(this);
        settingsScancodes = config.settingsScancodes;
        settingsKeycodes = config.settingsKeycodes;
        settingsPanel = config.settingsKeyPanel;
        keyShortcuts = config.keyShortcuts;
        stockHome.clear();
        if (!config.stockHomeRedirect.isEmpty()) {
            Intent home = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).setPackage(config.stockHomeRedirect);
            for (ResolveInfo ri : getPackageManager().queryIntentActivities(home, PackageManager.MATCH_DISABLED_COMPONENTS)) {
                stockHome.add(ri.activityInfo.name);
            }
        }
        SleepTimer.attach(this);
    }

    @Override
    public void onDestroy() {
        cancelSleep();
        SleepTimer.detach(this);
        super.onDestroy();
    }

    /** Starts the countdown to {@code endsAt} (uptimeMillis), replacing one that is running. */
    void armSleep(long endsAt) {
        cancelSleep();
        handler.postAtTime(sleepWarning, endsAt - SleepTimer.WARNING_MS);
        handler.postAtTime(sleepNow, endsAt);
    }

    void cancelSleep() {
        handler.removeCallbacks(sleepWarning);
        handler.removeCallbacks(sleepNow);
    }

    /**
     * Locks the screen, which puts the TV to sleep. This path is not yet verified on the projector: whether
     * GLOBAL_ACTION_LOCK_SCREEN sleeps an XGIMI, and whether it needs a secure lock set, is still untested. A refusal
     * (the action returns false, or Android is older than 9) shows "Not available" instead of failing silently.
     */
    private void sleepNow() {
        SleepTimer.finish();
        boolean slept = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                && performGlobalAction(GLOBAL_ACTION_LOCK_SCREEN);
        if (!slept) Toast.makeText(this, R.string.not_available, Toast.LENGTH_SHORT).show();
    }

    private boolean isSettingsKey(KeyEvent event) {
        if (event.getKeyCode() == KeyEvent.KEYCODE_SETTINGS) return true;
        for (int code : settingsScancodes) if (event.getScanCode() == code) return true;
        for (int code : settingsKeycodes) if (event.getKeyCode() == code) return true;
        return false;
    }

    /**
     * Starts the app's TV entry point, falling back to the phone one. A missing app only shows a toast:
     * the key is consumed either way, so a manufacturer handler never sees a shortcut button this
     * service owns (XGIMI's, for one, re-enables the stock launcher on each press).
     */
    private void launch(String pkg) {
        PackageManager pm = getPackageManager();
        Intent intent = pm.getLeanbackLaunchIntentForPackage(pkg);
        if (intent == null) intent = pm.getLaunchIntentForPackage(pkg);
        try {
            if (intent == null) throw new ActivityNotFoundException(pkg);
            startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, R.string.not_available, Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected boolean onKeyEvent(KeyEvent event) {
        String shortcut = keyShortcuts.get(event.getKeyCode());
        if (shortcut != null) {
            if (event.getAction() == KeyEvent.ACTION_UP && !event.isCanceled()) launch(shortcut);
            return true;
        }
        // The stock launcher handled the remote's Settings button; with it disabled the button does nothing.
        if (isSettingsKey(event)) {
            if (event.getAction() == KeyEvent.ACTION_UP && !event.isCanceled()) {
                Intent open = settingsPanel ? new Intent(this, QuickSettingsActivity.class)
                        : new Intent(Settings.ACTION_SETTINGS);
                startActivity(open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            }
            return true;
        }
        if (event.getKeyCode() != KeyEvent.KEYCODE_ALL_APPS) return false;
        if (event.getAction() == KeyEvent.ACTION_UP && !event.isCanceled()) {
            Intent home = new Intent(Intent.ACTION_MAIN)
                    .addCategory(Intent.CATEGORY_HOME)
                    .setPackage(getPackageName())
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            startActivity(home);
        }
        return true;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // stock_home_redirect: the firmware turned the stock launcher back on and its home screen came up.
        if (stockHome.isEmpty() || event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence cls = event.getClassName();
        if (cls != null && stockHome.contains(cls.toString())) {
            startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).setPackage(getPackageName())
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED));
        }
    }

    @Override
    public void onInterrupt() {
    }
}
