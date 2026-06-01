#-----------------------------------------------------------------------------
#                        Proprietary - Export Controlled
#
# Descriptions:
#   CH340 USB 4-Channel Relay Controller — tkinter GUI
#   Sends standard 4-byte serial commands to toggle relays ON/OFF.
#   Auto-detects CH340 port on launch; CH 1 defaults ON, CH 2-4 OFF.
#
# Author: Chinh Nguyen
#-----------------------------------------------------------------------------

import math
import time
import threading
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

BAUD_RATE   = 9600
NUM_RELAYS  = 4
DEFAULT_ON  = {1}          # Channel 1 ON at startup, rest OFF

# Device label shown below each relay panel (index matches channel number)
CHAN_LABELS = ["", "Edge HD Power", "GT81 Power", "Fan Power", "SPARE"]

# USB vendor IDs that identify CH340 / compatible chips
CH340_VIDS  = {0x1A86, 0x0403, 0x067B}

# Relay command header byte
CMD_HEADER  = 0xA0

# Fixed width (px) shared by the relay panel and its label box
PANEL_W     = 122
PANEL_H     = 150
LABEL_H     = 34
LABEL_RADI  = 8            # rounded-corner radius for label box
LED_SIZE    = 60
LED_CENTER  = LED_SIZE // 2
LED_RADIUS  = 13
LED_RAYS    = 10

LED_NO_COMM = "#555555"
LED_ON      = "#ffcc33"
LED_OFF     = "#79cfff"
LED_RAY     = "#ffe066"

FONT_TITLE  = ("Helvetica", 13, "bold")
FONT_CHAN   = ("Helvetica", 12, "bold")
FONT_BTN    = ("Helvetica", 11, "bold")
FONT_LABEL  = ("Helvetica", 10)
FONT_STAT   = ("Helvetica", 11)


#-----------------------------------------------------------------------------
# Build a 4-byte relay command packet
#
#   relay  : relay number 1-4
#   state  : True = ON, False = OFF
#   returns: bytes [header, relay, state, checksum]
#-----------------------------------------------------------------------------
def build_cmd(relay, state):
    relay_state = 0x01 if state else 0x00
    checksum    = (CMD_HEADER + relay + relay_state) & 0xFF
    return bytes([CMD_HEADER, relay, relay_state, checksum])


#-----------------------------------------------------------------------------
# Scan serial ports and return the first CH340-compatible port name.
# Returns None if no device is found.
#-----------------------------------------------------------------------------
def find_ch340():
    for port_info in serial.tools.list_ports.comports():
        if port_info.vid in CH340_VIDS:
            return port_info.device
        desc = (port_info.description or "").lower()
        if any(tag in desc for tag in ("ch340", "ch341", "usb serial", "usb-serial")):
            return port_info.device
    return None


#-----------------------------------------------------------------------------
# Draw a rounded rectangle on a Canvas using smooth polygon.
#
#   canvas        : tk.Canvas target
#   x1,y1,x2,y2  : bounding box
#   radius        : corner radius in pixels
#   **kw          : forwarded to create_polygon (fill, outline, width, …)
#-----------------------------------------------------------------------------
def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kw):
    pts = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2,          y1,
        x2,          y1 + radius,
        x2,          y2 - radius,
        x2,          y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1,          y2,
        x1,          y2 - radius,
        x1,          y1 + radius,
        x1,          y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


#=============================================================================
# RelayApp — main application window
#=============================================================================
class RelayApp(tk.Tk):

    #-------------------------------------------------------------------------
    # Initialise window, build UI, then attempt auto-connect
    #-------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.title("CH340 Relay Controller")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.ser_port    = None
        self.ser_lock    = threading.Lock()
        self.relay_state = [False] * (NUM_RELAYS + 1)   # 1-indexed
        self.comm_ok     = False

        self._build_ui()
        self._set_defaults()
        self._auto_connect()
        self.after(250, self._show_window)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    #-------------------------------------------------------------------------
    # Construct all widgets
    #-------------------------------------------------------------------------
    def _build_ui(self):
        tk.Label(self,
                 text="CH340 Relay Controller",
                 bg="#1e1e1e", fg="#aaaaaa",
                 font=FONT_TITLE).pack(pady=(10, 4))

        panel_frame = tk.Frame(self, bg="#1e1e1e")
        panel_frame.pack(padx=12, pady=4)

        self.led_list = [None] * (NUM_RELAYS + 1)
        self.btn_list = [None] * (NUM_RELAYS + 1)

        for i in range(1, NUM_RELAYS + 1):
            col_frame = tk.Frame(panel_frame, bg="#1e1e1e")
            col_frame.grid(row=0, column=i - 1, padx=5, pady=4)

            # ── Relay control box ─────────────────────────────────────────
            ch_frame = tk.Frame(col_frame,
                                bg="#2d2d2d",
                                highlightbackground="#444444",
                                highlightthickness=1)
            ch_frame.config(width=PANEL_W, height=PANEL_H)
            ch_frame.pack_propagate(False)
            ch_frame.pack(fill="x")   # stretches to match label box width

            tk.Label(ch_frame,
                     text=f"CH {i}",
                     bg="#2d2d2d", fg="#cccccc",
                     font=FONT_CHAN).pack(pady=(8, 4))

            led_cv = tk.Canvas(ch_frame, width=LED_SIZE, height=LED_SIZE,
                               bg="#2d2d2d", highlightthickness=0)
            led_cv.pack()
            ray_ids = self._draw_led_rays(led_cv)
            oval_id = led_cv.create_oval(
                                         LED_CENTER - LED_RADIUS,
                                         LED_CENTER - LED_RADIUS,
                                         LED_CENTER + LED_RADIUS,
                                         LED_CENTER + LED_RADIUS,
                                         fill="#333333",
                                         outline="#555555",
                                         width=2)
            led_cv.oval_id = oval_id
            led_cv.ray_ids = ray_ids
            led_cv.bind("<Button-1>", lambda evt, ch=i: self._toggle(ch))
            self.led_list[i] = led_cv

            tog_btn = tk.Button(ch_frame,
                                text="OFF", width=7,
                                height=2,
                                bg="#444444", fg="#cccccc",
                                activebackground="#555555",
                                font=FONT_BTN,
                                relief="flat", bd=0,
                                cursor="hand2",
                                command=lambda ch=i: self._toggle(ch))
            tog_btn.pack(pady=(6, 8))
            self.btn_list[i] = tog_btn

            # ── Device label box (rounded rectangle) ──────────────────────
            lbl_cv = tk.Canvas(col_frame,
                               width=PANEL_W, height=LABEL_H,
                               bg="#1e1e1e", highlightthickness=0)
            lbl_cv.pack(pady=(4, 0))

            draw_rounded_rect(lbl_cv,
                              2, 2, PANEL_W - 2, LABEL_H - 2,
                              radius=LABEL_RADI,
                              fill="#b8b8b8",
                              outline="#777777",
                              width=1)

            lbl_cv.create_text(PANEL_W // 2, LABEL_H // 2,
                               text=CHAN_LABELS[i],
                               fill="#000000",
                               font=FONT_LABEL)
            lbl_cv.bind("<Button-1>", lambda evt, ch=i: self._toggle(ch))
            lbl_cv.config(cursor="hand2")

        # ── Status / port bar ─────────────────────────────────────────────
        status_bar = tk.Frame(self, bg="#b8b8b8")
        status_bar.pack(fill="x", padx=12, pady=(6, 10))

        self.port_text = tk.StringVar(value="No device")
        self.stat_lbl  = tk.Label(status_bar,
                                  textvariable=self.port_text,
                                  bg="#b8b8b8", fg="#000000",
                                  font=FONT_STAT)
        self.stat_lbl.pack(side="left")

        tk.Button(status_bar,
                  text="Refresh Serial",
                  width=14,
                  height=2,
                  bg="#b8b8b8", fg="#000000",
                  activebackground="#c8c8c8",
                  font=FONT_BTN,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._auto_connect).pack(side="right")

    #-------------------------------------------------------------------------
    # Draw the LED radial lines in a hidden state and return the item list
    #-------------------------------------------------------------------------
    def _draw_led_rays(self, led_cv):
        ray_ids = []
        for i in range(LED_RAYS):
            angle = (2 * math.pi * i) / LED_RAYS
            in_rad = LED_RADIUS + 5
            out_rad = LED_RADIUS + 12
            x1 = LED_CENTER + math.cos(angle) * in_rad
            y1 = LED_CENTER + math.sin(angle) * in_rad
            x2 = LED_CENTER + math.cos(angle) * out_rad
            y2 = LED_CENTER + math.sin(angle) * out_rad
            ray_id = led_cv.create_line(
                x1, y1, x2, y2,
                fill=LED_RAY,
                width=2,
                capstyle=tk.ROUND,
                state="hidden",
            )
            ray_ids.append(ray_id)
        return ray_ids

    #-------------------------------------------------------------------------
    # Set the initial visible state before a serial connection is available
    #-------------------------------------------------------------------------
    def _set_defaults(self):
        for i in range(1, NUM_RELAYS + 1):
            is_on = i in DEFAULT_ON
            self.relay_state[i] = is_on
            self._update_led(i, is_on)

    #-------------------------------------------------------------------------
    # Set serial communication state and refresh all relay indicators
    #-------------------------------------------------------------------------
    def _set_comm(self, is_ready):
        self.comm_ok = is_ready
        for i in range(1, NUM_RELAYS + 1):
            self._update_led(i, self.relay_state[i])

    #-------------------------------------------------------------------------
    # Bring the window forward when launched by Finder or LaunchAgent
    #-------------------------------------------------------------------------
    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

    #-------------------------------------------------------------------------
    # Update LED colour and button label for one channel
    #-------------------------------------------------------------------------
    def _update_led(self, ch_num, is_on):
        led_cv    = self.led_list[ch_num]
        led_color = LED_NO_COMM
        ray_state = "hidden"
        btn_bg    = "#777777"
        btn_fg    = "#000000"
        btn_act   = "#888888"

        if self.comm_ok and is_on:
            led_color = LED_ON
            ray_state = "normal"
            btn_bg    = LED_ON
            btn_act   = "#ffd85c"
        elif self.comm_ok:
            led_color = LED_OFF
            btn_bg    = LED_OFF
            btn_act   = "#9cddff"

        for ray_id in led_cv.ray_ids:
            led_cv.itemconfig(ray_id, state=ray_state)

        led_cv.itemconfig(led_cv.oval_id, fill=led_color)

        self.btn_list[ch_num].config(
            text="ON"  if is_on else "OFF",
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_act,
        )

    #-------------------------------------------------------------------------
    # Open a serial connection to the given port name.
    # Returns True on success, False on failure.
    #-------------------------------------------------------------------------
    def _open_port(self, port_name):
        try:
            with self.ser_lock:
                if self.ser_port and self.ser_port.is_open:
                    self.ser_port.close()
                self.ser_port = serial.Serial(port_name, BAUD_RATE, timeout=1)
            self.port_text.set(f"Connected: {port_name}")
            self.stat_lbl.config(fg="#000000")
            self._set_comm(True)
            return True
        except serial.SerialException as exc:
            self.port_text.set(f"Error: {exc}")
            self.stat_lbl.config(fg="#000000")
            self._set_comm(False)
            return False

    #-------------------------------------------------------------------------
    # Send a relay command over the open serial port.
    # Returns True on success.
    #-------------------------------------------------------------------------
    def _send_cmd(self, ch_num, is_on):
        with self.ser_lock:
            if not self.ser_port or not self.ser_port.is_open:
                return False
            try:
                self.ser_port.write(build_cmd(ch_num, is_on))
                return True
            except serial.SerialException:
                self.comm_ok = False
                return False

    #-------------------------------------------------------------------------
    # Scan for CH340 device and connect, then push default relay states
    #-------------------------------------------------------------------------
    def _auto_connect(self):
        port_name = find_ch340()
        if port_name and self._open_port(port_name):
            self._push_defaults()
        else:
            self.port_text.set("No CH340 device found — check USB")
            self.stat_lbl.config(fg="#000000")
            self._set_comm(False)

    #-------------------------------------------------------------------------
    # Send the initial ON/OFF state to every relay after a fresh connection
    #-------------------------------------------------------------------------
    def _push_defaults(self):
        for i in range(1, NUM_RELAYS + 1):
            is_on = i in DEFAULT_ON
            time.sleep(0.05)
            if self._send_cmd(i, is_on):
                self.relay_state[i] = is_on
                self._update_led(i, is_on)
            else:
                self._set_comm(False)
                break

    #-------------------------------------------------------------------------
    # Toggle a relay ON<->OFF when the user clicks a button
    #-------------------------------------------------------------------------
    def _toggle(self, ch_num):
        new_state = not self.relay_state[ch_num]
        if self._send_cmd(ch_num, new_state):
            self.relay_state[ch_num] = new_state
            self._update_led(ch_num, new_state)
        else:
            self._set_comm(False)
            messagebox.showwarning(
                "Connection Lost",
                "Could not send command.\nClick Refresh Serial to retry.",
            )

    #-------------------------------------------------------------------------
    # Close serial port cleanly before the window is destroyed
    #-------------------------------------------------------------------------
    def _on_close(self):
        with self.ser_lock:
            if self.ser_port and self.ser_port.is_open:
                self.ser_port.close()
        self.destroy()


#-----------------------------------------------------------------------------
# Entry point
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    app = RelayApp()
    app.mainloop()
