import sqlite3
from abc import ABC
from io import BytesIO
from threading import Lock
from tkinter import *
from tkinter import messagebox

import cv2
import pandas as pd
from PIL import Image, ImageTk
from PIL.ImageFile import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
cnx = sqlite3.connect("products.sqlite")


class Visualize:
    def __init__(self):
        self._products = Visualize.read_all_products()

    """ SQL Stuff. """

    def add_product(self, product, photo):
        self._products.loc[len(self._products.index)] = [
            product.get_name(),
            product.get_purch_date(),
            product.get_supplier(),
            product.get_expiration_date(),
            product.get_storage_code(),
            product.get_info(),
            product.get_material_list(),
            str(photo)
        ]

        self._products.to_sql(name="products", con=cnx)

    def find_product(self, storage_code):
        all_rows = []
        for index, row in self._products.iterrows():
            if str(row["Storage Code"]) == storage_code:
                all_rows.append(row)

        if len(all_rows) > 0:
            return all_rows[-1]

    @staticmethod
    def read_all_products():
        try:
            return pd.read_sql("SELECT * FROM products", con=cnx)
        except (FileNotFoundError, pd.errors.DatabaseError, sqlite3.OperationalError):
            return pd.DataFrame(
                columns=['Name', 'Purch Date', 'Supplier', 'Expiration Date', 'Storage Code', 'Info', 'Material List',
                         "Photo"],
            )


class RawMaterials(ABC):
    def __init__(self, name, purch_date, supplier, expiration_date, storage_code, info):
        self._name = name
        self._purch_date = purch_date
        self._supplier = supplier
        self._expiration_date = expiration_date
        self._storage_code = storage_code
        self._info = info

    """ Getter methods """

    def get_name(self):
        return self._name

    def get_purch_date(self):
        return self._purch_date

    def get_supplier(self):
        return self._supplier

    def get_expiration_date(self):
        return self._expiration_date

    def get_storage_code(self):
        return self._storage_code

    def get_info(self):
        return self._info

    """ Setter methods """

    def set_name(self, value):
        self._name = value

    def set_purch_date(self, value):
        self._purch_date = value

    def set_supplier(self, value):
        self._supplier = value

    def set_expiration_date(self, value):
        self._expiration_date = value

    def set_storage_code(self, value):
        self._storage_code = value

    def set_info(self, value):
        self._info = value


class Products(RawMaterials):
    def __init__(self, name, purch_date, supplier, expiration_date, storage_code, info, material_list):
        super().__init__(name, purch_date, supplier, expiration_date, storage_code, info)
        self._material_list = material_list

    """Get and Set methods for new attribute"""

    def get_material_list(self):
        return self._material_list

    def set_material_list(self, value):
        self._material_list = value


if __name__ == "__main__":
    # The main window.

    root = Tk()
    root.geometry("1000x600")
    root.title("Product Database")

    # Storage Code

    Label(root, text="Storage Code").place(x=40, y=30)
    storage_code_inp = Entry(width=30)
    storage_code_inp.place(x=40, y=50)

    # Name

    Label(root, text="Name").place(x=40, y=230)
    name_inp = Entry(width=30)
    name_inp.place(x=40, y=250)

    # Supplier

    Label(root, text="Supplier").place(x=40, y=80)
    supplier_inp = Entry(width=30)
    supplier_inp.place(x=40, y=100)

    # Purchase Date

    Label(root, text="Purchase Date").place(x=40, y=130)
    purch_inp = Entry(width=30)
    purch_inp.place(x=40, y=150)

    # Expiration Date

    Label(root, text="Expiration Date").place(x=40, y=180)
    exp_date_inp = Entry(width=30)
    exp_date_inp.place(x=40, y=200)

    # Info

    Label(root, text="Info").place(x=40, y=280)
    info_inp = Entry(width=30)
    info_inp.place(x=40, y=300)

    # Materials

    Label(root, text="Materials List").place(x=40, y=330)
    materials_inp = Entry(width=30)
    materials_inp.place(x=40, y=350)

    # The video label.

    label = Label(root)
    Label(root, text="Photo").place(x=300, y=20)
    label.place(x=300, y=50)

    # Visualize.
    v = Visualize()

    # Helpers.

    recording_lock = Lock()
    recording = False
    last_frame: Image = None
    cam_btn = None

    # Start the capture.
    cap = cv2.VideoCapture(0)
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture("video.mp4")


    def show_frames(first_time=False):
        global recording_lock
        global recording
        global cap
        global last_frame
        global cam_btn

        # If clicked for the first time.
        if first_time:
            with recording_lock:
                recording = True

        # Return if not recording.
        with recording_lock:
            if not recording:
                cam_btn.place(x=40, y=500)
                return

        # Read the frame.
        ret, frame = cap.read()
        if not ret:
            with recording_lock:
                cap = cv2.VideoCapture("video.mp4")
                cam_btn.place(x=40, y=500)
                recording = False
            return

        # Convert frame to Image.
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Convert image to PhotoImage
        img_tk = ImageTk.PhotoImage(image=img)
        label.imgtk = img_tk
        label.configure(image=img_tk)

        # Set the last frame.
        last_frame = img

        # Repeat after an interval to capture continuously
        label.after(50, show_frames)
        cam_btn.place_forget()


    def add_product():
        global recording
        global recording_lock
        global cap
        global last_frame
        global v

        # Return if no cam started.
        if not recording:
            messagebox.showerror(title="Error", message="You need to open camera first.")
            return

        # Get inputs.
        inputs = {
            "name": name_inp.get(),
            "supplier": supplier_inp.get(),
            "purch_date": purch_inp.get(),
            "expiration_date": exp_date_inp.get(),
            "storage_code": storage_code_inp.get(),
            "info": info_inp.get(),
            "material_list": materials_inp.get()
        }

        # Check inputs for empty str.
        for val in inputs.values():
            if not val:
                messagebox.showerror(title="Error", message="You need to fill all fields.")
                return

        # Lock the next frame lock.
        with recording_lock:
            output_buff = BytesIO()
            last_frame.save(output_buff, format="PNG")

            # Hex
            img_str = output_buff.getvalue().hex(" ", 1).strip("\n")

            # Add new product.
            product = Products(**inputs)
            v.add_product(product, img_str)

        messagebox.showinfo(title="Success", message="Added new product.")


    def find_product():
        global recording
        global recording_lock
        global cap
        global last_frame
        global v
        global cam_btn

        # Check storage code.
        storage_code = storage_code_inp.get()
        if not storage_code:
            messagebox.showerror(title="Error", message="You need to enter a valid storage code.")
            return

        # Get the product.
        product_row = v.find_product(storage_code)
        if product_row is None:
            messagebox.showerror(title="Error", message="No products found with this storage code.")
            return

        # Not recording.
        with recording_lock:
            recording = False
            cam_btn.place(x=40, y=500)

        # Clear fields.
        name_inp.delete(0, END)
        purch_inp.delete(0, END)
        supplier_inp.delete(0, END)
        exp_date_inp.delete(0, END)
        storage_code_inp.delete(0, END)
        info_inp.delete(0, END)
        materials_inp.delete(0, END)

        # Set fields.
        name_inp.insert(0, product_row.get("Name"))
        purch_inp.insert(0, product_row.get("Purch Date"))
        supplier_inp.insert(0, product_row.get("Supplier"))
        exp_date_inp.insert(0, product_row.get("Expiration Date"))
        storage_code_inp.insert(0, product_row.get("Storage Code"))
        info_inp.insert(0, product_row.get("Info"))
        materials_inp.insert(0, product_row.get("Material List"))

        # Decode photo.
        frame = bytes.fromhex(product_row.get("Photo").strip("\n"))

        # Convert frame to Image.
        img = Image.open(BytesIO(frame))

        # img.save("bruh.png", format="PNG")

        # Convert image to PhotoImage
        img_tk = ImageTk.PhotoImage(image=img)
        label.imgtk = img_tk
        label.configure(image=img_tk)

        cam_btn.place(x=40, y=500)
        messagebox.showinfo(title="Success", message="Product found in the database.")


    # Buttons

    add_btn = Button(text="Add New Product", width=27, command=add_product)
    add_btn.place(x=40, y=400)

    find_btn = Button(text="Find Product", width=27, command=find_product)
    find_btn.place(x=40, y=450)

    cam_btn_img = ImageTk.PhotoImage(Image.open("photo-camera.png").resize((20, 20), Image.LANCZOS))
    cam_btn = Button(text="Open Camera", width=194, image=cam_btn_img, command=lambda: show_frames(first_time=True))
    cam_btn.place(x=40, y=500)

    root.mainloop()
