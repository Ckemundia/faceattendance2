import os
import sqlite3
import datetime
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import face_recognition
import util
import csv



class App:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x600+350+100")
        self.main_window.title("Facial Recognition Attendance System")

        self.db_path = 'face_data.db'
        self.log_path = './log.txt'

        self.initialize_db()

        # Unit Entry Field
        self.unit_label = util.get_text_label(self.main_window, "Enter Unit Name:")
        self.unit_label.place(x=750, y=50)

        self.unit_entry = util.get_entry_text(self.main_window)
        self.unit_entry.place(x=750, y=100)

        self.login_button_main_window = util.get_button(self.main_window, 'Login', 'green', self.login)
        self.login_button_main_window.place(x=750, y=200)

        self.logout_button_main_window = util.get_button(self.main_window, 'Logout', 'red', self.logout)
        self.logout_button_main_window.place(x=750, y=300)

        self.register_new_user_button_main_window = util.get_button(
            self.main_window, 'Register New User', 'gray', self.register_new_user, fg='black'
        )
        self.register_new_user_button_main_window.place(x=750, y=400)

        self.show_attendance_button = util.get_button(self.main_window, 'Show Attendance', 'blue', self.show_attendance)
        self.show_attendance_button.place(x=750, y=500)

        self.webcam_label = util.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=0, width=700, height=500)

        self.add_webcam(self.webcam_label)

    def initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                student_id TEXT PRIMARY KEY,
                embedding BLOB
            )
        """)

        # Create attendance table with unit_name column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                unit_name TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES users(student_id)
            )
        """)

        conn.commit()
        conn.close()

    def add_webcam(self, label):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)

        self._label = label
        self.process_webcam()

    def process_webcam(self):
        ret, frame = self.cap.read()
        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)
        self._label.after(20, self.process_webcam)

    def get_unit_name(self):
        """Fetch the entered unit name"""
        return self.unit_entry.get("1.0", "end-1c").strip()

    def add_img_to_label(self, label):
        """Captures the most recent webcam image and updates the label"""
        if hasattr(self, "most_recent_capture_pil"):
            imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
            label.imgtk = imgtk
            label.configure(image=imgtk)
            self.register_new_user_capture = self.most_recent_capture_arr.copy()
        else:
            util.msg_box("Error", "No image captured yet. Please try again.")

    def login(self):
        student_id = util.recognize(self.most_recent_capture_arr, self.db_path)
        unit_name = self.get_unit_name()

        if not unit_name:
            util.msg_box('Error', 'Please enter a unit name before logging in.')
            return

        if student_id in ['unknown_person', 'no_persons_found']:
            util.msg_box('Error', 'Unknown user. Please register a new user or try again.')
        else:
            util.msg_box('Welcome back!', f'Welcome, Student ID: {student_id}. Unit: {unit_name}')

            # Log login event in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO attendance (student_id, unit_name, action) VALUES (?, ?, ?)",
                           (student_id, unit_name, 'login'))
            conn.commit()
            conn.close()

    def logout(self):
        student_id = util.recognize(self.most_recent_capture_arr, self.db_path)
        unit_name = self.get_unit_name()

        if not unit_name:
            util.msg_box('Error', 'Please enter a unit name before logging out.')
            return

        if student_id in ['unknown_person', 'no_persons_found']:
            util.msg_box('Error', 'Unknown user. Please register a new user or try again.')
        else:
            util.msg_box('Goodbye!', f'Goodbye, Student ID: {student_id}. Unit: {unit_name}')

            # Log logout event in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO attendance (student_id, unit_name, action) VALUES (?, ?, ?)",
                           (student_id, unit_name, 'logout'))
            conn.commit()
            conn.close()

    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")

        self.accept_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Accept', 'green',
                                                                      self.accept_register_new_user)
        self.accept_button_register_new_user_window.place(x=750, y=300)

        self.try_again_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Try Again',
                                                                         'red', self.try_again_register_new_user)
        self.try_again_button_register_new_user_window.place(x=750, y=400)

        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)

        self.add_img_to_label(self.capture_label)

        self.entry_text_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)

        self.text_label_register_new_user = util.get_text_label(self.register_new_user_window,
                                                                'Please, enter Student ID:')
        self.text_label_register_new_user.place(x=750, y=70)

    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()

    def accept_register_new_user(self):
        student_id = self.entry_text_register_new_user.get(1.0, "end-1c").strip()
        if not student_id:
            util.msg_box('Error', 'Student ID cannot be empty!')
            return

        embeddings = face_recognition.face_encodings(self.register_new_user_capture)
        if len(embeddings) == 0:
            util.msg_box('Error', 'No face detected. Try again!')
            return

        embeddings = embeddings[0]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (student_id, embedding) VALUES (?, ?)", (student_id, embeddings.tobytes()))
        conn.commit()
        conn.close()

        util.msg_box('Success!', 'User was registered successfully!')
        self.register_new_user_window.destroy()

    def show_attendance(self):
        logs = util.get_attendance_logs(self.db_path)

        if not logs:
            util.msg_box("Attendance Log", "No attendance records found.")
            return

        # Define the file path in the same directory as the script
        file_path = os.path.join(os.getcwd(), "attendance_log.csv")

        # Write attendance logs to CSV file
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Student ID", "Unit Name", "Action", "Timestamp"])  # CSV Header

            for log in logs:
                if len(log) == 4:  # Ensure correct data format
                    writer.writerow(log)
                else:
                    writer.writerow(["Incomplete record", *log])  # Handle missing data

        util.msg_box("Export Successful", f"Attendance log saved as:\n{file_path}")

    def start(self):
        self.main_window.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
