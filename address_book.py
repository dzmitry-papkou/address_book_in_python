import csv
import json
import sys
import os

from sqlalchemy import Column, Integer, String, MetaData, Table, create_engine,  desc
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.state import InstanceState

from PyQt6 import QtCore
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QPushButton, QLabel, QListWidget, QLineEdit, QComboBox, QListWidgetItem)
from PyQt6.QtGui import QFont


# base class for the database
Base = declarative_base()

# designes for the main window
class DesignPatterns():
     
    # counter lable designe
    def lables_counter():
        font = QFont("Arial", 20)
        font.setBold(True)
        return font
    
    # general lable designe
    def lables_main():
        font = QFont("Arial", 10)
        font.setBold(True)
        return font
    
# main window ui and functionality of widgets 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.address_book = AddressBook()
        self.start_main_window()
    
    # main window ui
    def start_main_window(self):
        self.address_book.main_window_ui(self)
        self.address_book.createButton.clicked.connect(self.contact_create_edit_window)
        self.address_book.searchButton.clicked.connect(self.contact_search_window)
        self.address_book.exportDataButton.clicked.connect(self.contact_export_window)
        self.address_book.listWidget.itemClicked.connect(self.contact_display_window)
        
    # contact create/edit window ui
    def contact_create_edit_window(self, item, action="create"):
        self.setEnabled(False)
        self.contact_create = ContactCreateEdit(self.unfreeze_main_window, item, action)
        self.contact_create.saveButton.clicked.connect(self.contact_create.save_contact)
        self.contact_create.saveButton.clicked.connect(self.contact_create.close)
        self.contact_create.saveButton.clicked.connect(self.unfreeze_main_window)
        self.contact_create.cancelButton.clicked.connect(self.contact_create.close)
        self.contact_create.cancelButton.clicked.connect(self.unfreeze_main_window)
        if action == "create":
            self.contact_create.saveButton.clicked.connect(self.address_book.add_to_the_list)
        if action == "edit":
            self.contact_create.cancelButton.clicked.connect(self.address_book.remove_from_the_list)
            self.contact_create.saveButton.clicked.connect(self.address_book.update_contact_in_the_list)
        if action == "search+edit":
            self.contact_create.cancelButton.clicked.connect(lambda: ContactDataBase.remove_contact_from_database(item))
            self.contact_create.cancelButton.clicked.connect(self.address_book.number_of_contacts_decriase)
            self.contact_create.cancelButton.clicked.connect(self.address_book.display_contact)
            self.contact_create.saveButton.clicked.connect(self.address_book.display_contact)
        self.contact_create.show()
        
    # contact search window ui
    def contact_search_window(self):
        self.setEnabled(False)
        self.contact_search = ContactSearch(self.unfreeze_main_window)
        self.contact_search.searchButton.clicked.connect(self.contact_search.search_contact_in_database)
        self.contact_search.searchList.itemClicked.connect(self.contact_search.show_contact_data)
        self.contact_search.cancelButton.clicked.connect(self.contact_search.close)
        self.contact_search.cancelButton.clicked.connect(self.unfreeze_main_window)
        self.contact_search.editButton.clicked.connect(self.contact_search.close)
        self.contact_search.editButton.clicked.connect(lambda: self.contact_create_edit_window(self.contact_search.show_contact_data(), "search+edit"))
        self.contact_search.show()
       
    # contact display window ui
    def contact_display_window(self, item):
        self.setEnabled(False)
        self.contact_display = ContactDisplay(self.unfreeze_main_window, item)
        self.contact_display.cancelButton.clicked.connect(self.contact_display.close)
        self.contact_display.cancelButton.clicked.connect(self.unfreeze_main_window)
        self.contact_display.editButton.clicked.connect(self.contact_display.close)
        self.contact_display.editButton.clicked.connect(lambda: self.contact_create_edit_window(item, "edit"))
        
        self.contact_display.show()
    
    # contact export window ui
    def contact_export_window(self):
        self.setEnabled(False)
        self.contact_export = ContactExport(self.unfreeze_main_window)
        self.contact_export.cancelButton.clicked.connect(self.contact_export.close)
        self.contact_export.exportButton.clicked.connect(self.contact_export.export_contacts_to_file)
        self.contact_export.exportButton.clicked.connect(self.contact_export.close)
        self.contact_export.files_in_directory.itemClicked.connect(self.contact_export.exist_file_update)
        self.contact_export.show()
        
    # unfreeze main window
    def unfreeze_main_window(self):
        # Unfreeze the main window
        self.setEnabled(True)
    
    # close all windows if main window is closed
    def closeEvent(self, event):
        for widget in QApplication.topLevelWidgets():
            if widget is not self:
                widget.close()
        event.accept()
        
        
# the class that represents the program's address book and its functionality
class AddressBook(QWidget):
    def __init__(self):
        super().__init__()
        self.contacts = ContactDataBase()
        self.comboSpinner = QComboBox(self)
        self.label = QLabel(self)
        self.design_counter = DesignPatterns.lables_counter()
        self.design_label = DesignPatterns.lables_main()
        self.counter=0
        
    # ___ main window ui ___
    def main_window_ui(self, MainWindow):
        MainWindow.setWindowTitle("Address Book")
        MainWindow.setFixedSize(460, 420)
        
        # ___ list to display buttons ___
        self.listWidget = QListWidget(MainWindow)
        self.listWidget.setGeometry(180, 20, 260, 380)
        self.listWidget.setObjectName("listWidget")
        self.display_contact()
        
        # ___ display number of contacts ___
        self.label = QLabel("Number of contacts:", MainWindow)
        self.label.setGeometry(10, 20, 160, 16)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(self.design_label)
        
        # counter of contacts
        self.counterLable = QLabel(MainWindow)
        self.counterLable.setGeometry(10, 50, 160, 20)
        self.counterLable.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.counterLable.setText("{0}".format(self.counter))
        self.counterLable.setFont(self.design_counter)
        
        # ___ spin element to sort contacts ___
        self.comboSpinner = QComboBox(MainWindow)
        self.comboSpinner.setGeometry(15, 90, 145, 26)
        self.comboSpinner.setObjectName("comboSpinner")
        self.comboSpinner.addItem("Default list")
        self.comboSpinner.addItem("Sort by first name")
        self.comboSpinner.addItem("Sort by surname")
        self.comboSpinner.currentIndexChanged.connect(self.display_contact)
        
        # ___ search button ___
        self.searchButton = QPushButton("Search", MainWindow)
        self.searchButton.setGeometry(40, 140, 95, 36)
        self.searchButton.setObjectName("searchButton")
       
        
       
       # ___ create button ___
        self.createButton = QPushButton("Create", MainWindow)
        self.createButton.setGeometry(40, 190, 95, 36)
        self.createButton.setObjectName("createButton")
        self.createButton.setText("Create")
        
       
        
        # ___ export data button ___
        self.exportDataButton = QPushButton("Export Data",MainWindow)
        self.exportDataButton.setGeometry(40, 240, 95, 36)
        self.exportDataButton.setObjectName("exportDataButton")
        
        
    # ___ contact create/edit window ui according spinner ___
    def display_contact(self):
        self.listWidget.clear()
        action = self.comboSpinner.currentText()
        self.counter = 0
        contacts = []
        
        if action == "Default list":
            contacts = self.contacts.display_database_contacts("default")
        elif action == "Sort by first name":
            contacts = self.contacts.display_database_contacts("sort_by_first_name")
        elif action == "Sort by surname":
            contacts = self.contacts.display_database_contacts("sort_by_surname")
        else:
            contacts = self.contacts.display_database_contacts("default")
            
        for contact in contacts:
            self.counter += 1
            item = QListWidgetItem(f"{contact.first_name} {contact.surname}")
            item.contact_id = contact.id
            self.listWidget.addItem(item)

    # udpate contact in the list
    def update_contact_in_the_list(self):
        updated_contact = self.listWidget.currentItem()
        updated_contact_index = self.listWidget.row(updated_contact)
        self.listWidget.takeItem(updated_contact_index)
        new_last_contact = ContactDataBase.get_contact_by_id(updated_contact)
        item = QListWidgetItem(f"{new_last_contact.first_name} {new_last_contact.surname}")
        item.contact_id = new_last_contact.id
        self.listWidget.insertItem(updated_contact_index, item)
        
    # add contact to the list     
    def add_to_the_list(self):
        new_contact = self.contacts.get_new_contact() 
        item = QListWidgetItem(f"{new_contact.first_name} {new_contact.surname}")
        item.contact_id = new_contact.id
        self.listWidget.addItem(item)  
        self.counter += 1
        self.counterLable.setText("{0}".format(self.counter))
    
    # remove contact from the list
    def remove_from_the_list(self):
        contact_for_delete = self.listWidget.currentItem()
        self.contacts.remove_contact_from_database(contact_for_delete)
        self.listWidget.takeItem(self.listWidget.row(contact_for_delete))
        self.counter -= 1
        self.counterLable.setText("{0}".format(self.counter))
    
    # decrease number of contacts in the list after search window
    def number_of_contacts_decriase(self):
        self.counter -= 1
        self.counterLable.setText("{0}".format(self.counter))

# ___ contact search window ___
class ContactSearch(QWidget):
    def __init__(self, unfreeze_main_window_function):
        super().__init__()
        self.unfreeze_main_window_function = unfreeze_main_window_function
        self.searchList = QListWidget(self)
        self.start_search_ui()
        
    # ___ contact search window ui ___   
    def start_search_ui(self):
        
        self.setWindowTitle("Contact Search")
        self.setFixedSize(340, 210)
        
        # search button
        self.searchButton = QPushButton("Search",self)
        self.searchButton.setGeometry(10, 10, 70, 30)
        
        # search field
        self.name_edit = QLineEdit(self)
        self.name_edit.setGeometry(90, 10, 240, 30)
        
        # search list
        self.searchList.setGeometry(10, 50, 320, 150)
        
        # connect search button with search function
        self.contact_data = QLabel(self)
        self.contact_data.setGeometry(10, 190, 320, 160)
        
        self.editButton = QPushButton("Edit", self)
        self.editButton.setGeometry(250, 320, 70, 30)
        
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.setGeometry(170, 320, 70, 30)
        
    # ___ search function ___
    def search_contact_in_database(self):
        
        search_text = self.name_edit.text()
        contacts = ContactDataBase.contact_search(search_text)
        self.searchList.clear()
        for contact in contacts:
            
            item = QListWidgetItem(f"{contact.first_name} {contact.surname}")
            item.contact_id = contact.id
            self.searchList.addItem(item)
    
    # display contact data in the search window
    def show_contact_data(self):
        self.setFixedSize(340, 360)
        item = self.searchList.currentItem()
        contact = ContactDataBase.get_contact_by_id(item)
        
        self.contact_data.setText(
                           f"First name: {contact.first_name}\n"
                           f"Last name: {contact.surname}\n"
                           f"Email: {contact.email}\n"
                           f"Phone: {contact.phone_number}\n"
                           F"Workplace: {contact.workplace}")
        return item
    
    # close search window
    def closeEvent(self, event):
            self.unfreeze_main_window_function()
            event.accept()

# contact create/edit window
class ContactCreateEdit(QWidget):
    def __init__(self, unfreeze_main_window_function, item, action):
        super().__init__()
        self.unfreeze_main_window_function = unfreeze_main_window_function
        self.item = item
        self.action = action
        self.font_lables = DesignPatterns.lables_main()
        self.start_create_ui()
        
    # contact create/edit window ui
    def start_create_ui(self):    
        # Set layout
        self.setWindowTitle("New Contact")
        self.setFixedSize(340, 350)
        
        # lable first name
        self.nameLable = QLabel("First name:", self)
        self.nameLable.setGeometry(10, 0, 320, 30)
        self.nameLable.setFont(self.font_lables)
        
        # first name field edit
        self.name_edit = QLineEdit(self)
        self.name_edit.setGeometry(10, 30, 320, 30)
        
        # lable last name
        self.surnameLable = QLabel("Last name:", self)
        self.surnameLable.setGeometry(10, 60, 320, 30)
        self.surnameLable.setFont(self.font_lables)
        
        # last name field edit
        self.last_name_edit = QLineEdit(self)
        self.last_name_edit.setGeometry(10, 90, 320, 30)
        
        # lable email
        self.emailLabel = QLabel("Email:", self)
        self.emailLabel.setGeometry(10, 120, 320, 30)
        self.emailLabel.setFont(self.font_lables)
        
        # email field edit
        self.email_edit = QLineEdit(self)
        self.email_edit.setGeometry(10, 150, 320, 30)
        
        # lable phone number
        self.phone_numberLable = QLabel("Phone number:", self)
        self.phone_numberLable.setGeometry(10, 180, 320, 30)
        self.phone_numberLable.setFont(self.font_lables)
       
        # phone number field edit
        self.phone_number_edit = QLineEdit(self)
        self.phone_number_edit.setGeometry(10, 210, 320, 30)
        
        # label workplace
        self.workplaceLable = QLabel("Workplace:", self)
        self.workplaceLable.setGeometry(10, 240, 320, 30)
        self.workplaceLable.setFont(self.font_lables)
        
        # workplace field edit
        self.workplace_edit = QLineEdit(self)
        self.workplace_edit.setGeometry(10, 270, 320, 30)
        
        # buttons 
        # ___ cancel button ___
        self.cancelButton = QPushButton("Cancel",self)
        self.cancelButton.setGeometry(180, 310, 70, 30)
        
        # save button
        self.saveButton = QPushButton("Save",self)
        self.saveButton.setGeometry(260, 310, 70, 30)
        
        # edit contact from search or directly from main window
        if self.action == "edit" or self.action == "search+edit":
            self.setWindowTitle("Edit Contact")
            self.saveButton.setText("Update")
            self.cancelButton.setText("Delete")
            contact = ContactDataBase.get_contact_by_id(self.item)
            self.last_name_edit.setText(contact.surname)
            self.name_edit.setText(contact.first_name)
            self.email_edit.setText(contact.email)
            self.phone_number_edit.setText(contact.phone_number)
            self.workplace_edit.setText(contact.workplace)
        
            
    # save contact to database 
    def save_contact(self):
        first_name = self.name_edit.text()
        surname = self.last_name_edit.text()
        phone_number = self.phone_number_edit.text()
        email = self.email_edit.text()
        workplace = self.workplace_edit.text()
        # add single contact to list
        if self.action == "edit" or self.action == "search+edit":
            ContactDataBase.update_contact_in_database(self.item, first_name, surname, phone_number, email, workplace)
        elif self.action == "create":
            ContactDataBase.add_contact_to_database(first_name, surname, phone_number, email, workplace)
        # clear fields
        self.name_edit.clear()
        self.last_name_edit.clear()
        self.phone_number_edit.clear()
        self.email_edit.clear()
        self.workplace_edit.clear()
      
    # delete contact from database  
    def closeEvent(self, event):
        self.unfreeze_main_window_function()
        event.accept()
        
# display contact details
class ContactDisplay(QWidget):
    def __init__(self, unfreeze_main_window_function, item):
        super().__init__()
        self.unfreeze_main_window_function = unfreeze_main_window_function
        self.item = item
        self.start_display_ui()
    
    # display contact details ui
    def start_display_ui(self):
        self.setWindowTitle("Contact Details")
        self.setFixedSize(340, 140)
        
        # contact name display
        self.contact_data = QLabel(self)
        self.on_item_clicked()    
        # ___ cancel button ___
        self.cancelButton = QPushButton("Cancel",self)
        self.cancelButton.setGeometry(180, 100, 70, 30)
        
        # ___ edit contact button ___
        self.editButton = QPushButton("Edit",self)
        self.editButton.setGeometry(260, 100, 70, 30)
        
        
    def on_item_clicked(self):
        contact = ContactDataBase.get_contact_by_id(self.item)
        self.contact_data.setGeometry(10, 0, 320, 100)
    # Update the details label with the details of the selected contact
        self.contact_data.setText(
                           f"First name: {contact.first_name}\n"
                           f"Last name: {contact.surname}\n"
                           f"Email: {contact.email}\n"
                           f"Phone: {contact.phone_number}\n"
                           F"Workplace: {contact.workplace}")
        
    # close window
    def closeEvent(self, event):
        self.unfreeze_main_window_function()
        event.accept()
        
# export contacts to file
class ContactExport(QWidget):
    def __init__(self, unfreeze_main_window_function):
        super().__init__()
        self.unfreeze_main_window_function = unfreeze_main_window_function
        self.font_lables = DesignPatterns.lables_main()
        self.start_export_ui()
        
    # export contacts ui
    def start_export_ui(self):
        self.setWindowTitle("Contacts Export")
        self.setFixedSize(340, 220)
        
        # file name label
        self.file_name_label = QLabel("File name:", self)
        self.file_name_label.setGeometry(10, 0, 100, 30)
        self.file_name_label.setFont(self.font_lables)
        
        # file name field edit
        self.file_name = QLineEdit(self)
        self.file_name.setGeometry(10, 25, 240, 30)
        
        # extention spinner
        self.file_extentionSpinner = QComboBox(self)
        self.file_extentionSpinner.setGeometry(260, 25, 70, 30)
        self.file_extentionSpinner.setObjectName("comboExtentionSpinner")
        self.file_extentionSpinner.addItem(".txt")
        self.file_extentionSpinner.addItem(".json")
        self.file_extentionSpinner.addItem(".csv")
        self.file_extentionSpinner.addItem(".xml")
        self.file_extentionSpinner.currentIndexChanged.connect(self.show_files_in_directory)
        
        # list of files in directory
        self.files_in_directory = QListWidget(self)
        self.files_in_directory.setGeometry(10, 65, 320, 105)
        self.show_files_in_directory()
        
        # buttons
        self.cancelButton = QPushButton("Cancel",self)
        self.cancelButton.setGeometry(180, 180, 70, 30)
        
        self.exportButton = QPushButton("Export",self)
        self.exportButton.setGeometry(260, 180, 70, 30)
    
    # export contacts to file
    def export_contacts_to_file(self):
        save_path = os.path.join(new_folder, self.file_name.text() + self.file_extentionSpinner.currentText())
        ContactDataBase.export_contacts_from_database_to_file(save_path)
        
    # show files in directory
    def show_files_in_directory(self):
        self.files_in_directory.clear()
        extension = self.file_extentionSpinner.currentText()
        for file in os.listdir(new_folder):
            if file.endswith(extension):
                self.files_in_directory.addItem(file)
    
    # update file name field edit
    def exist_file_update(self):
        selected_file = self.files_in_directory.currentItem().text()
        self.file_name.setText(selected_file[:-4])
        
    # close window
    def closeEvent(self, event):
        self.unfreeze_main_window_function()
        event.accept()

# database class 
class ContactDataBase(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(30))
    surname = Column(String(30))
    email = Column(String(50))
    phone_number = Column(String(20))
    workplace = Column(String(50))
    
    
    # add contact to database
    @staticmethod
    def add_contact_to_database(first_name="", last_name="", phone_number="", email="", workplace=""):  
        new_contact = ContactDataBase(first_name=first_name, surname=last_name, phone_number=phone_number, email=email, workplace=workplace)
        session.add(new_contact)
        session.commit()
    
    # display contact from database
    @staticmethod
    def display_database_contacts(action="default"):
        
        contacts = []
        if action == "default":
            contacts = session.query(ContactDataBase).all()
        elif action == "sort_by_first_name":
            contacts = session.query(ContactDataBase).order_by(ContactDataBase.first_name).all()
        elif action == "sort_by_surname":
            contacts = session.query(ContactDataBase).order_by(ContactDataBase.surname).all()  
        return contacts
    
    # get new contact by id
    @staticmethod
    def get_new_contact():
        contact = session.query(ContactDataBase).order_by(desc(ContactDataBase.id)).first()
        return contact    
    
    # get contact by id
    @staticmethod
    def get_contact_by_id(item):
        contact_id = item.contact_id
        contact = session.query(ContactDataBase).filter_by(id=contact_id).first()
        return contact
    
    # update database data
    @staticmethod
    def update_contact_in_database(item, first_name="", last_name="", phone_number="", email="", workplace=""):
        contact = ContactDataBase.get_contact_by_id(item)
        contact.first_name = first_name
        contact.surname = last_name
        contact.phone_number = phone_number
        contact.email = email
        contact.workplace = workplace
        session.commit()
       
    # remove contact from database
    @staticmethod
    def remove_contact_from_database(item):
        contact = ContactDataBase.get_contact_by_id(item)
        session.delete(contact)
        session.commit()
    
    # search contact in database
    @staticmethod
    def contact_search(search_text):
        contacts = []
        key_items = search_text.split()
        for item in key_items:
            contacts_search_by_key = session.query(ContactDataBase).filter((ContactDataBase.first_name.like("%" + item + "%")) |(ContactDataBase.surname.like("%"+item+"%")) |(ContactDataBase.phone_number.like("%"+item+"%")) |(ContactDataBase.email.like("%"+item+"%")) |(ContactDataBase.workplace.like("%"+item+"%"))).all()
            contacts = list(set(contacts + contacts_search_by_key))
        
        return contacts
    
    # export contacts from database to file
    @staticmethod
    def export_contacts_from_database_to_file(file_name):
        extention_type = file_name.split(".")[-1]
        contacts = ContactDataBase.display_database_contacts()
        # txt file
        if extention_type == "txt":
            with open(file_name, "w") as file:
                for contact in contacts:
                    file.write(f"{contact.first_name}\t {contact.surname}\t {contact.phone_number}\t {contact.email}\t {contact.workplace}\t\n")
        # json file
        elif extention_type == "json":
            with open(file_name, "w") as file:
                 json.dump(contacts, file, cls=ContactEncoder, ensure_ascii=False, indent=5)
        # csv file  
        elif extention_type == "csv":
            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["first_name", "surname", "phone_number", "email", "workplace"])
                for contact in contacts:
                    writer.writerow([contact.first_name, contact.surname, contact.email,contact.phone_number, contact.workplace])
        # xml file
        elif extention_type == "xml":
            with open(file_name, "w") as file:
                file.write("<contacts>\n")
                for contact in contacts:
                    file.write(f"\t<contact>\n\t\t<first_name>{contact.first_name}</first_name>\n\t\t<surname>{contact.surname}</surname>\n\t\t<phone_number>{contact.phone_number}</phone_number>\n\t\t<email>{contact.email}</email>\n\t\t<workplace>{contact.workplace}</workplace>\n\t</contact>\n")
                file.write("</contacts>")
        
# json encoder class to serialize database objects (sqlalchemy model objects)
class ContactEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # If obj is a SQLAlchemy model object, return its dictionary representation
            return obj.__dict__
        elif isinstance(obj, InstanceState):
            # Exclude InstanceState objects from being serialized
            return None
        return json.JSONEncoder.default(self, obj)
       

if __name__ == '__main__':
    # Create database if not exists if exists connect to it
    

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a new directory called "new_folder" in the script directory
    new_folder = os.path.join(script_dir, "files")
    new_database_folder = os.path.join(new_folder, "database")
    if not os.path.exists(new_folder):
        os.makedirs(new_database_folder)
    elif not os.path.exists(new_database_folder):
        os.makedirs(new_database_folder)
    else:
        pass
    
    # database exists or not
    database_path = os.path.join(new_database_folder, 'address_book.db')
    engine = create_engine('sqlite:///' + database_path)
    if os.path.exists(database_path):
        pass
    else:
        
        metadata = MetaData()
        contacts = Table('contacts', metadata,
                         Column('id', Integer, primary_key=True),
                         Column('first_name', String(30)),
                         Column('surname', String(30)),
                         Column('email', String(50)),
                         Column('phone_number', String(20)),
                         Column('workplace', String(50)),
        )
        metadata.create_all(engine)
        
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.lastWindowClosed.connect(app.quit)
    sys.exit(app.exec())
    