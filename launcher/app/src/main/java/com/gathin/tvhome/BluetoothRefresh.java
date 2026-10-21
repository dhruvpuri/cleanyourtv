package com.gathin.tvhome;

import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

/**
 * Restarts Bluetooth so paired speakers, headphones and keyboards reconnect: switching the adapter off and on
 * makes the TV page every bonded device again. The Bluetooth pill runs it on a press.
 *
 * Needs BLUETOOTH_ADMIN and BLUETOOTH (declared up to Android 11): Android 13 stopped letting apps toggle the
 * adapter, so on newer TVs this only shows "Not available".
 */
final class BluetoothRefresh {
    /** Longest wait for the restart to finish before the adapter is switched back on anyway. */
    private static final long TIMEOUT_MS = 10_000;

    private static boolean running;

    private BluetoothRefresh() {
    }

    /** Off, then on. A press while a restart is under way is ignored; an adapter that is already off is just switched on. */
    @SuppressWarnings("deprecation")   // enable()/disable() are deprecated since Android 13, where they stop working
    static void run(Context context) {
        Context app = context.getApplicationContext();
        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null) {
            toast(app, R.string.not_available);
            return;
        }
        if (running) return;
        Handler handler = new Handler(Looper.getMainLooper());
        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context c, Intent intent) {
                int state = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, BluetoothAdapter.ERROR);
                try {
                    if (state == BluetoothAdapter.STATE_OFF) adapter.enable();
                    else if (state == BluetoothAdapter.STATE_ON) finish(app, this, handler);
                } catch (SecurityException e) {
                    finish(app, this, handler);
                }
            }
        };
        running = true;
        try {
            if (adapter.getState() == BluetoothAdapter.STATE_OFF) {
                running = false;
                adapter.enable();
                toast(app, R.string.bluetooth_restarting);
                return;
            }
            app.registerReceiver(receiver, new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED));
            // Never leave Bluetooth off: if the restart stalls, put the adapter back and stop listening.
            handler.postDelayed(() -> {
                try {
                    if (adapter.getState() != BluetoothAdapter.STATE_ON) adapter.enable();
                } catch (SecurityException ignored) {
                }
                finish(app, receiver, handler);
            }, TIMEOUT_MS);
            toast(app, R.string.bluetooth_restarting);
            if (!adapter.disable()) finish(app, receiver, handler);
        } catch (SecurityException e) {
            finish(app, receiver, handler);
            toast(app, R.string.not_available);
        }
    }

    private static void finish(Context app, BroadcastReceiver receiver, Handler handler) {
        running = false;
        handler.removeCallbacksAndMessages(null);
        try {
            app.unregisterReceiver(receiver);
        } catch (IllegalArgumentException ignored) {   // never registered, or already removed
        }
    }

    private static void toast(Context app, int message) {
        Toast.makeText(app, message, Toast.LENGTH_SHORT).show();
    }
}
