import tkinter as tk
from tkinter import messagebox
from dronekit import connect, VehicleMode
import threading
import time
from style import AppStyle


class GroundControlStation:
    def __init__(self, root):
        self.root = root
        AppStyle.configure_window(root)

        self.vehicle = None
        self.busy = False
        self.closing = False
        self.create_widgets()
        self.update_controls()
        self.refresh_status()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        connection_frame = AppStyle.make_section(self.root, "Connection")
        connection_frame.pack(fill="x", padx=16, pady=(14, 8))
        AppStyle.make_label(connection_frame, "Connection string:").grid(row=0, column=0, padx=6, pady=7, sticky="w")
        self.connection_entry = AppStyle.make_entry(connection_frame, width=30)
        self.connection_entry.insert(0, "127.0.0.1:14550")
        self.connection_entry.grid(row=0, column=1, padx=6, pady=7, sticky="ew")
        self.connect_button = AppStyle.make_button(connection_frame, "Connect", self.connect_vehicle)
        self.connect_button.grid(row=0, column=2, padx=6, pady=7)

        self.disconnect_button = AppStyle.make_button(connection_frame, "Close Connection", self.disconnect_vehicle)
        self.disconnect_button.grid(row=1, column=2, padx=6, pady=7)
        connection_frame.columnconfigure(1, weight=1)

        
        mode_frame = AppStyle.make_section(self.root, "Flight Modes", padx=10, pady=12)
        mode_frame.pack(fill="x", padx=16, pady=8)
        self.mode_buttons = []
        modes = ["GUIDED", "LOITER", "STABILIZE", "LAND", "RTL"]
        for col, mode in enumerate(modes):
            button = AppStyle.make_button(
                mode_frame,
                mode,
                lambda selected_mode=mode: self.change_mode(
                    selected_mode
                ),
            )
            button.grid(row=0, column=col, padx=4, pady=5, sticky="ew")
            mode_frame.columnconfigure(col, weight=1)
            self.mode_buttons.append(button)

        
        takeoff_frame = AppStyle.make_section(self.root, "Takeoff")
        takeoff_frame.pack(fill="x", padx=16, pady=8)
        AppStyle.make_label(takeoff_frame, "Altitude:").grid(row=0, column=0, padx=6, pady=7, sticky="w")
        self.altitude_entry = AppStyle.make_entry(takeoff_frame, width=10)
        self.altitude_entry.insert(0, "10")
        self.altitude_entry.grid(row=0, column=1, padx=6, pady=7, sticky="w")
        self.takeoff_button = AppStyle.make_button(takeoff_frame, "Takeoff", self.takeoff)
        self.takeoff_button.grid(row=0, column=2, padx=12, pady=7)
        takeoff_frame.columnconfigure(1, weight=1)

        
        arm_frame = tk.Frame(self.root, bg=AppStyle.WINDOW_BG)
        arm_frame.pack(fill="x", padx=16, pady=8)
        self.arm_button = AppStyle.make_button(arm_frame, "Arm", self.toggle_arm, bg=AppStyle.ARM_BUTTON_BG,)
        self.arm_button.config(width=18, pady=8)
        self.arm_button.pack()

        
        status_frame = AppStyle.make_section(self.root, "Vehicle Status")
        status_frame.pack(fill="x", padx=16, pady=8)
        self.connection_status_label = AppStyle.make_status_label(status_frame, "Connection: Disconnected")
        self.arming_status_label = AppStyle.make_status_label(status_frame, "Arming: Unknown")
        self.mode_label = AppStyle.make_status_label(status_frame, "Flight mode: Unknown")
        self.flight_status_label = AppStyle.make_status_label(status_frame, "Flight status: Unknown")
        self.altitude_label = AppStyle.make_status_label(status_frame, "Altitude: Unknown")
        self.armable_label = AppStyle.make_status_label(status_frame, "Ready to arm: Unknown")
        self.status_label = tk.Label(
            self.root,
            text="Status: Disconnected",
            wraplength=600,
            justify="center",
            bg=AppStyle.WINDOW_BG,
            fg=AppStyle.SECONDARY_COLOR,
            padx=10,
            pady=5,
        )
        self.status_label.pack(fill="x", padx=16, pady=(2, 10))

    

    def set_status(self, message, error=False):
        self.status_label.config(
            text=f"Status: {message}",
            fg=(
                AppStyle.ERROR_COLOR
                if error else AppStyle.SUCCESS_COLOR
            ),
        )

    def report_error(self, message):
        self.set_status("Operation failed.", error=True)
        messagebox.showerror("DroneKit Error", message)

    def run_in_background(self, task, success_message=None):
        if self.busy:
            return
        self.busy = True
        self.update_controls()

        def worker():
            try:
                task()
                if success_message:
                    self.root.after(
                        0,
                        lambda msg=success_message: self.set_status(msg),
                    )
            except Exception as exc:
                error_text = str(exc)
                self.root.after(
                    0,
                    lambda msg=error_text: self.report_error(msg),
                )
            finally:
                self.root.after(0, self.finish_operation)
        threading.Thread(target=worker, daemon=True).start()

    def finish_operation(self):
        self.busy = False
        self.update_controls()

    def connect_vehicle(self):
        if self.vehicle is not None:
            return
        connection_string = self.connection_entry.get().strip()
        if not connection_string:
            self.set_status("Enter a connection string.", error=True)
            return
        self.set_status("Connecting...")
        def task():
            vehicle = connect(
                connection_string,
                wait_ready=True,
                timeout=30,
            )
            if self.closing:
                vehicle.close()
                return
            self.root.after(0, lambda: self.save_vehicle(vehicle))
        self.run_in_background(task)

    def save_vehicle(self, vehicle):
        if self.closing:
            vehicle.close()
            return
        self.vehicle = vehicle
        self.set_status("Connected to vehicle.")
        self.update_controls()

    def disconnect_vehicle(self):
        if self.vehicle is None:
            self.set_status("No active connection.", error=True)
            return
        vehicle = self.vehicle
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
                if altitude is not None and altitude > 0.5:
                    raise RuntimeError("The vehicle appears airborne. Land before disarming.")
                vehicle.armed = False
                deadline = time.time() + 10
                while vehicle.armed and time.time() < deadline:
                    time.sleep(0.2)
                if vehicle.armed:
                    raise RuntimeError("Vehicle did not disarm in time.")
            else:
                if vehicle.mode.name not in ["GUIDED", "LOITER", "STABILIZE"]:
                    return
                vehicle.armed = True
                deadline = time.time() + 15
                while not vehicle.armed and time.time() < deadline:
                    time.sleep(0.2)
                if not vehicle.armed:
                    raise RuntimeError("Vehicle did not arm. Check ArduPilot pre-arm errors.")
        self.run_in_background(task, "Arming state updated.")

    def change_mode(self, mode):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("Connect first.", error=True)
            return
        if mode == "GUIDED" and not vehicle.is_armable:
            messagebox.showwarning(
                "Vehicle Not Ready",
                "The vehicle may not be ready for flight. "
                "Check its status before takeoff.",
            )

        def task():
            vehicle.mode = VehicleMode(mode)
            deadline = time.time() + 5
            while vehicle.mode.name != mode and time.time() < deadline:
                time.sleep(0.2)
            if vehicle.mode.name != mode:
                raise RuntimeError(f"Vehicle did not change to {mode} mode.")
        self.run_in_background(task, f"Flight mode set to {mode}.")

    

    def takeoff(self):
        vehicle = self.vehicle
        if vehicle is None:
            self.set_status("Connect first.", error=True)
            return
        try:
            altitude = float(self.altitude_entry.get())
        except ValueError:
            self.set_status("Enter a valid altitude.", error=True)
            return
        if not 1 <= altitude <= 80:
            self.set_status("Altitude must be between 1 and 80 metres.", error=True)
            return
        if vehicle.mode.name != "GUIDED":
            messagebox.showwarning("Wrong Flight Mode.")
            return
        if not vehicle.armed:
            messagebox.showwarning(
                "Vehicle Disarmed",
                "Arm the vehicle before taking off.",
            )
            return

        def task():
            vehicle.simple_takeoff(altitude)
            deadline = time.time() + 60
            while time.time() < deadline:
                current_alt = (
                    vehicle.location.global_relative_frame.alt
                )
                if current_alt is not None and current_alt >= altitude * 0.95:
                    return
                if not vehicle.armed or vehicle.mode.name != "GUIDED":
                    raise RuntimeError(
                        f"Takeoff interrupted! "
                        f"Armed: {vehicle.armed}, "
                        f"Mode: {vehicle.mode.name}"
                    )
                time.sleep(0.5)
            raise RuntimeError("Target altitude was not reached.")
        self.run_in_background(task, f"Reached {altitude:g} metres.")


    def refresh_status(self):
        vehicle = self.vehicle
        if vehicle is not None:
            try:
                if vehicle.is_armable:
                    armable = "Yes"
                elif vehicle.armed:
                    armable = "No (armed)"
                else:
                    armable = "No"
                altitude = vehicle.location.global_relative_frame.alt
                altitude_text = (
                    f"{altitude:.1f} m"
                    if altitude is not None else "Unavailable"
                )
                self.connection_status_label.config(text="Connection: Connected")
                self.arming_status_label.config(text=f"Arming: {'Armed' if vehicle.armed else 'Disarmed'}")
                self.mode_label.config(text=f"Flight mode: {vehicle.mode.name}")
                self.flight_status_label.config(
                    text=(
                        "Flight status: Airborne"
                        if altitude is not None and altitude > 0.5
                        else "Flight status: On ground / low altitude"
                    )
                )
                self.altitude_label.config(text=f"Altitude: {altitude_text}")
                self.armable_label.config(text=f"Ready to arm: {armable}")
            except Exception:
                self.connection_status_label.config(text="Connection: Telemetry unavailable")
        else:
            self.connection_status_label.config(text="Connection: Disconnected")
            self.arming_status_label.config(text="Arming: Unknown")
            self.mode_label.config(text="Flight mode: Unknown")
            self.flight_status_label.config(text="Flight status: Unknown")
            self.altitude_label.config(text="Altitude: Unknown")
            self.armable_label.config(text="Ready to arm: Unknown")
        self.update_controls()
        if not self.closing:
            self.root.after(1000, self.refresh_status)


    def update_controls(self):
        connected = self.vehicle is not None
        self.connection_entry.config(state="disabled" if connected or self.busy 
                                     else "normal")
        self.connect_button.config(state="disabled" if connected or self.busy 
                                   else "normal")
        self.disconnect_button.config(state="normal" if connected and not self.busy and not self.vehicle.armed 
                                      else "disabled")
        for button in self.mode_buttons:
            button.config(state="normal" if connected and not self.busy 
                          else "disabled")
        is_armed = connected and self.vehicle.armed
        arm_allowed = (
            connected
            and not self.busy
            and self.vehicle.mode.name not in ["LAND", "RTL"]
            and (is_armed or self.vehicle.is_armable)
            )
        self.arm_button.config(
            state="normal" if arm_allowed else "disabled",
            text="Disarm" if is_armed else "Arm"
        )
        takeoff_allowed = (
            connected
            and not self.busy
            and self.vehicle.armed
            and self.vehicle.mode.name == "GUIDED"
        )
        self.takeoff_button.config(state="normal" if takeoff_allowed else "disabled")


    def on_close(self):
        if self.busy:
            messagebox.showwarning(
                "Operation in Progress",
                "Wait for the current operation to finish before closing.",
            )
            return
        if self.vehicle is not None:
            if self.vehicle.armed:
                messagebox.showwarning(
                    "Vehicle Armed",
                    "The vehicle is armed. Land and disarm it before "
                    "closing this application.",
                )
                return
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
