import threading
import time
import tkinter as tk
from tkinter import messagebox

from dronekit import connect, VehicleMode
from style import AppStyle


class GroundControlStation:
    MODES = ("GUIDED", "LOITER", "STABILIZE", "LAND", "RTL")
    ARMING_MODES = ("GUIDED", "LOITER", "STABILIZE")
    RC_MODES = ("STABILIZE", "LOITER")
    RC_MIN, RC_MAX, RC_CENTER = 1000, 2000, 1500
    RC_STEP, RC_UPDATE_MS = 20, 50

    def __init__(self, root):
        self.root = root
        AppStyle.configure_window(root)
        self.vehicle = None
        self.busy = False
        self.closing = False

        self.rc_values = {"1": 1500, "2": 1500, "3": 1000, "4": 1500}
        self.rc_pressed_keys = set()
        self.rc_keyboard_enabled = tk.BooleanVar(value=True)
        self.rc_channel_widgets = {}

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all("<KeyPress>", self.on_key_press)
        self.root.bind_all("<KeyRelease>", self.on_key_release)
        self.update_controls()
        self.refresh_status()
        self.update_rc_channels()

    
    def create_widgets(self):
        connection = AppStyle.make_section(
            self.root, "Connection", padx=10, pady=6)
        connection.pack(fill="x", padx=12, pady=(10, 5))
        AppStyle.make_label(
            connection, "Connection string:").grid(
                row=0, column=0, padx=6, pady=5, sticky="w")
        self.connection_entry = AppStyle.make_entry(
            connection, width=25)
        self.connection_entry.insert(0, "127.0.0.1:14550")
        self.connection_entry.grid(
            row=0, column=1, padx=6, pady=5, sticky="ew")
        self.connect_button = AppStyle.make_button(
            connection, "Connect", self.connect_vehicle)
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)
        self.disconnect_button = AppStyle.make_button(
            connection, "Disconnect", self.disconnect_vehicle)
        self.disconnect_button.grid(row=0, column=3, padx=5, pady=5)
        connection.columnconfigure(1, weight=1)
        body = tk.Frame(self.root, bg=AppStyle.WINDOW_BG)
        body.pack(fill="both", expand=True, padx=12, pady=4)
        left = tk.Frame(body, bg=AppStyle.WINDOW_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right = tk.Frame(body, bg=AppStyle.WINDOW_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=6)
        body.rowconfigure(0, weight=1)
        modes = AppStyle.make_section(
            left, "Flight Modes", padx=8, pady=7)
        modes.pack(fill="x", pady=4)
        self.mode_buttons = []
        for col, mode in enumerate(self.MODES):
            button = AppStyle.make_button(
                modes, mode,
                lambda selected=mode: self.change_mode(selected))
            button.grid(row=0, column=col, padx=2, pady=4, sticky="ew")
            modes.columnconfigure(col, weight=1)
            self.mode_buttons.append(button)
        takeoff = AppStyle.make_section(
            left, "Takeoff", padx=8, pady=7)
        takeoff.pack(fill="x", pady=4)
        AppStyle.make_label(
            takeoff, "Target altitude (m):").grid(
                row=0, column=0, padx=5, pady=5, sticky="w")
        self.altitude_entry = AppStyle.make_entry(takeoff, width=8)
        self.altitude_entry.insert(0, "10")
        self.altitude_entry.grid(row=0, column=1, padx=5, pady=5)
        self.takeoff_button = AppStyle.make_button(
            takeoff, "Takeoff", self.takeoff)
        self.takeoff_button.grid(row=0, column=2, padx=8, pady=5)
        arm_frame = tk.Frame(left, bg=AppStyle.WINDOW_BG)
        arm_frame.pack(fill="x", pady=5)
        self.arm_button = AppStyle.make_button(
            arm_frame, "Arm", self.toggle_arm,
            bg=AppStyle.ARM_BUTTON_BG)
        self.arm_button.config(width=18, pady=7)
        self.arm_button.pack()
        status = AppStyle.make_section(
            left, "Vehicle Status", padx=10, pady=6)
        status.pack(fill="both", expand=True, pady=4)
        self.connection_status_label = AppStyle.make_status_label(
            status, "Connection: Disconnected")
        self.arming_status_label = AppStyle.make_status_label(
            status, "Arming: Unknown")
        self.mode_label = AppStyle.make_status_label(
            status, "Flight mode: Unknown")
        self.flight_status_label = AppStyle.make_status_label(
            status, "Flight status: Unknown")
        self.altitude_label = AppStyle.make_status_label(
            status, "Altitude: Unknown")
        self.armable_label = AppStyle.make_status_label(
            status, "Ready to arm: Unknown")
        self.create_rc_section(right)
        self.status_label = tk.Label(
            self.root,
            text="Status: Disconnected",
            wraplength=900,
            justify="center",
            bg=AppStyle.WINDOW_BG,
            fg=AppStyle.SECONDARY_COLOR,
            padx=8,
            pady=5
        )
        self.status_label.pack(fill="x", padx=12, pady=(2, 8))

    
    def create_rc_section(self, parent):
        section = AppStyle.make_section(
            parent, "Keyboard RC Control", padx=8, pady=8)
        section.pack(fill="both", expand=True, pady=4)
        definitions = (
            ("1", "ROLL", "Left / Right", 1500),
            ("2", "PITCH", "Up / Down", 1500),
            ("3", "THROTTLE", "W / S", 1000),
            ("4", "YAW", "A / D", 1500),
        )
        for col, (channel, name, keys, initial) in enumerate(definitions):
            widgets = AppStyle.make_rc_channel(
                section, channel, name, keys, initial)
            widgets["frame"].grid(
                row=1, column=col, padx=3, pady=4, sticky="n")
            self.rc_channel_widgets[channel] = widgets
        for col in range(4):
            section.columnconfigure(col, weight=1)

    def set_status(self, message, error=False):
        self.status_label.config(
            text=f"Status: {message}",
            fg=AppStyle.ERROR_COLOR if error else AppStyle.SUCCESS_COLOR)

    def report_error(self, message):
        self.set_status("Operation failed.", error=True)
        messagebox.showerror("DroneKit Error", message)

    def run_in_background(self, task, success_message=None):
        if self.busy or self.closing:
            return
        self.busy = True
        self.update_controls()
        def worker():
            try:
                task()
                if success_message and not self.closing:
                    self.root.after(
                        0, lambda msg=success_message: self.set_status(msg))
            except Exception as exc:
                if not self.closing:
                    message = str(exc)
                    self.root.after(
                        0, lambda msg=message: self.report_error(msg))
            finally:
                if not self.closing:
                    self.root.after(0, self.finish_operation)

        threading.Thread(target=worker, daemon=True).start()

    def finish_operation(self):
        self.busy = False
        self.update_controls()

    def connect_vehicle(self):
        if self.vehicle is not None:
            return
        address = self.connection_entry.get().strip()
        if not address:
            self.set_status("Enter a connection string.", error=True)
            return
        self.set_status("Connecting...")
        def task():
            vehicle = connect(address, wait_ready=True, timeout=30)
            if self.closing:
                vehicle.close()
                return
            self.root.after(0, lambda v=vehicle: self.save_vehicle(v))
        self.run_in_background(task)

    def save_vehicle(self, vehicle):
        if self.closing:
            vehicle.close()
            return
        self.vehicle = vehicle
        self.set_status("Connected to vehicle.")
        self.update_controls()

    def disconnect_vehicle(self):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("No active connection.", error=True)
            return
        if vehicle.armed:
            messagebox.showwarning(
                "Vehicle Armed",
                "Land and disarm the vehicle before disconnecting.")
            return
        self.clear_rc_overrides(vehicle)
        self.rc_keyboard_enabled.set(False)
        self.rc_pressed_keys.clear()
        self.vehicle = None
        self.update_controls()
        self.set_status("Closing connection...")
        self.run_in_background(vehicle.close, "Disconnected.")

    def toggle_arm(self):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("Connect first.", error=True)
            return
        def task():
            if vehicle.armed:
                altitude = vehicle.location.global_relative_frame.alt
                if altitude is None or altitude > 0.5:
                    raise RuntimeError(
                        "Disarming is allowed only when the vehicle is "
                        "confirmed on the ground (altitude <= 0.5 m).")
                self.clear_rc_overrides(vehicle)
                vehicle.armed = False
                deadline = time.time() + 10
                while vehicle.armed and time.time() < deadline:
                    time.sleep(0.2)
                if vehicle.armed:
                    raise RuntimeError("Vehicle did not disarm in time.")
            else:
                if vehicle.mode.name not in self.ARMING_MODES:
                    raise RuntimeError(
                        "Arming is allowed only in GUIDED, LOITER "
                        "or STABILIZE mode.")
                if not vehicle.is_armable:
                    raise RuntimeError(
                        "Vehicle is not armable. Check pre-arm status.")
                vehicle.armed = True
                deadline = time.time() + 15
                while not vehicle.armed and time.time() < deadline:
                    time.sleep(0.2)
                if not vehicle.armed:
                    raise RuntimeError(
                        "Vehicle did not arm. Check ArduPilot pre-arm errors.")
        self.run_in_background(task, "Arming state updated.")

    def change_mode(self, mode):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("Connect first.", error=True)
            return
        def task():
            vehicle.mode = VehicleMode(mode)
            deadline = time.time() + 5
            while vehicle.mode.name != mode and time.time() < deadline:
                time.sleep(0.2)
            if vehicle.mode.name != mode:
                raise RuntimeError(f"Vehicle did not change to {mode}.")
            if mode not in self.RC_MODES:
                self.clear_rc_overrides(vehicle)
        self.run_in_background(task, f"Flight mode set to {mode}.")


    def takeoff(self):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("Connect first.", error=True)
            return
        try:
            target = float(self.altitude_entry.get())
        except ValueError:
            self.set_status("Enter a valid altitude.", error=True)
            return
        if not 1 <= target <= 80:
            self.set_status("Altitude must be between 1 and 80 metres.",
                            error=True)
            return
        if vehicle.mode.name != "GUIDED":
            messagebox.showwarning(
                "Wrong Flight Mode", "Takeoff is available only in GUIDED.")
            return
        if not vehicle.armed:
            messagebox.showwarning(
                "Vehicle Disarmed", "Arm the vehicle before taking off.")
            return
        def task():
            vehicle.simple_takeoff(target)
            deadline = time.time() + 60
            while time.time() < deadline:
                altitude = vehicle.location.global_relative_frame.alt
                if altitude is not None and altitude >= target * 0.95:
                    return
                if not vehicle.armed or vehicle.mode.name != "GUIDED":
                    raise RuntimeError(
                        "Takeoff interrupted: "
                        f"armed={vehicle.armed}, mode={vehicle.mode.name}")
                time.sleep(0.5)
            raise RuntimeError("Target altitude was not reached.")
        self.run_in_background(task, f"Reached {target:g} metres.")


    def on_key_press(self, event):
        if not self.rc_keyboard_enabled.get():
            return
        if isinstance(event.widget, (tk.Entry, tk.Spinbox)):
            return
        key = event.keysym.lower()
        if key in {"left", "right", "up", "down", "w", "s", "a", "d"}:
            self.rc_pressed_keys.add(key)

    def on_key_release(self, event):
        self.rc_pressed_keys.discard(event.keysym.lower())

    def toggle_keyboard_control(self):
        self.rc_pressed_keys.clear()
        if not self.rc_keyboard_enabled.get():
            self.reset_rc_values()
            if self.vehicle is not None:
                self.clear_rc_overrides(self.vehicle)
            self.set_status("Keyboard RC control disabled.")
        else:
            self.set_status(
                "Keyboard RC enabled. Overrides are sent only when armed "
                "in STABILIZE or LOITER.")
        self.draw_rc_channels()

    def reset_rc_values(self):
        self.rc_values.update({"1": 1500, "2": 1500, "3": 1000, "4": 1500})

    def change_channel(self, channel, increase_key, decrease_key, recenter):
        value = self.rc_values[channel]
        if increase_key in self.rc_pressed_keys:
            value += self.RC_STEP
        elif decrease_key in self.rc_pressed_keys:
            value -= self.RC_STEP
        elif recenter:
            if value > 1500:
                value = max(1500, value - self.RC_STEP)
            elif value < 1500:
                value = min(1500, value + self.RC_STEP)
        self.rc_values[channel] = max(self.RC_MIN, min(self.RC_MAX, value))

    def process_rc_keys(self):
        self.change_channel("1", "right", "left", True)
        self.change_channel("2", "up", "down", True)
        self.change_channel("3", "w", "s", False)
        self.change_channel("4", "d", "a", True)

    @staticmethod
    def clear_rc_overrides(vehicle):
        try:
            vehicle.channels.overrides = {}
        except Exception:
            pass

    def update_rc_channels(self):
        if self.closing:
            return
        vehicle = self.vehicle
        enabled = self.rc_keyboard_enabled.get()

        if enabled:
            self.process_rc_keys()

        allowed = (
            enabled and vehicle is not None and not self.busy
            and vehicle.armed and vehicle.mode.name in self.RC_MODES
        )
        if allowed:
            try:
                vehicle.channels.overrides = self.rc_values.copy()
            except Exception as exc:
                self.set_status(f"RC override error: {exc}", error=True)
        elif vehicle is not None:
            self.clear_rc_overrides(vehicle)

        self.draw_rc_channels()
        self.root.after(self.RC_UPDATE_MS, self.update_rc_channels)

    def draw_rc_channels(self):
        for channel, widgets in self.rc_channel_widgets.items():
            value = self.rc_values[channel]
            canvas = widgets["canvas"]
            width, height = int(canvas["width"]), int(canvas["height"])
            canvas.delete("all")

            y_value = height - (value - self.RC_MIN) / (
                self.RC_MAX - self.RC_MIN) * height
            center_y = height - (1500 - self.RC_MIN) / (
                self.RC_MAX - self.RC_MIN) * height

            canvas.create_line(
                4, center_y, width - 4, center_y,
                fill=AppStyle.RC_CENTER_COLOR, dash=(2, 2))
            canvas.create_rectangle(
                10, y_value, width - 10, height - 2,
                fill=AppStyle.RC_BAR_COLOR, outline="")
            widgets["value_label"].config(text=f"{value} us")

    def refresh_status(self):
        if self.closing:
            return
        vehicle = self.vehicle
        if vehicle is None:
            self.connection_status_label.config(text="Connection: Disconnected")
            self.arming_status_label.config(text="Arming: Unknown")
            self.mode_label.config(text="Flight mode: Unknown")
            self.flight_status_label.config(text="Flight status: Unknown")
            self.altitude_label.config(text="Altitude: Unknown")
            self.armable_label.config(text="Ready to arm: Unknown")
        else:
            try:
                armed = vehicle.armed
                altitude = vehicle.location.global_relative_frame.alt
                self.connection_status_label.config(text="Connection: Connected")
                self.arming_status_label.config(
                    text=f"Arming: {'Armed' if armed else 'Disarmed'}")
                self.mode_label.config(text=f"Flight mode: {vehicle.mode.name}")
                self.flight_status_label.config(
                    text=("Flight status: Airborne"
                          if altitude is not None and altitude > 0.5
                          else "Flight status: On ground / low altitude"))
                self.altitude_label.config(
                    text=(f"Altitude: {altitude:.1f} m"
                          if altitude is not None
                          else "Altitude: Unavailable"))
                self.armable_label.config(
                    text=f"Ready to arm: {'Yes' if vehicle.is_armable else 'No'}")
            except Exception:
                self.connection_status_label.config(
                    text="Connection: Telemetry unavailable")
        self.update_controls()
        self.root.after(1000, self.refresh_status)

    def update_controls(self):
        connected = self.vehicle is not None
        vehicle = self.vehicle

        self.connection_entry.config(
            state="disabled" if connected or self.busy else "normal")
        self.connect_button.config(
            state="disabled" if connected or self.busy else "normal")
        self.disconnect_button.config(
            state=("normal" if connected and not self.busy
                   and not vehicle.armed else "disabled"))

        for button in self.mode_buttons:
            button.config(
                state="normal" if connected and not self.busy else "disabled")
        armed = connected and vehicle.armed
        can_arm = (
            connected and not armed and not self.busy
            and vehicle.mode.name in self.ARMING_MODES
            and vehicle.is_armable
        ) if connected else False
        can_disarm = False
        if armed and not self.busy:
            altitude = vehicle.location.global_relative_frame.alt
            can_disarm = altitude is not None and altitude <= 0.5
        self.arm_button.config(
            state="normal" if can_arm or can_disarm else "disabled",
            text="Disarm" if armed else "Arm")
        can_takeoff = (
            connected and not self.busy and vehicle.armed
            and vehicle.mode.name == "GUIDED"
        ) if connected else False
        self.takeoff_button.config(
            state="normal" if can_takeoff else "disabled")
        self.altitude_entry.config(
            state="normal" if can_takeoff else "disabled")

    def on_close(self):
        if self.busy:
            messagebox.showwarning(
                "Operation in Progress",
                "Wait for the current operation to finish before closing.")
            return
        if self.vehicle is not None:
            if self.vehicle.armed:
                messagebox.showwarning(
                    "Vehicle Armed",
                    "Land and disarm the vehicle before closing this app.")
                return
            self.clear_rc_overrides(self.vehicle)
            try:
                self.vehicle.close()
            except Exception:
                pass
            self.vehicle = None
        self.closing = True
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GroundControlStation(root)
    root.mainloop()
