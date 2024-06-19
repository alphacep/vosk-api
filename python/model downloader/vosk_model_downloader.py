#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import ttk
import tkinter.filedialog as filedialog

import os
import zipfile
import urllib3
import requests

from bs4 import BeautifulSoup
from threading import Thread

class model_downloader():
    def __init__(self):

        self.model_dir = os.path.abspath(os.path.dirname(__file__))
       
        self.execution_method = None

        self.url = None

        self.gui_x = 650
        self.gui_y = 450
        self.gui_font = "Raleway"
        
        self.gui_master = tk.Tk()
        self.gui_master.title('VOSK model downloader')
        self.gui_master.geometry('{}x{}'.format(self.gui_x, self.gui_y))

        self.model_to_download = None
        self.languages, self.model_names = self.load_models()

        style = ttk.Style()
        style.map('TCombobox', fieldbackground=[('readonly','white')])
        style.map('TCombobox', selectbackground=[('readonly', 'white')])
        style.map('TCombobox', selectforeground=[('readonly', 'black')])

        self.gui_master.grid_rowconfigure(4, weight=1)
        self.gui_master.grid_columnconfigure(0, weight=1)
        
        self.model_frame = tk.Frame(self.gui_master, padx=10, pady=10)
        self.model_frame.grid(row=0, sticky="news")
        
        self.directory_frame = tk.Frame(self.gui_master, padx=10, pady=10)
        self.directory_frame.grid(row=1, sticky="news")
        
        self.control_frame = tk.Frame(self.gui_master)
        self.control_frame.grid(row=2, sticky="news")

        self.model_frame.grid_rowconfigure(4, weight=1)
        self.model_frame.grid_columnconfigure(1, weight=1)

        self.lbl_welcome = tk.Label(self.model_frame, text = 'The VOSK model downloader!', font= self.gui_font)
        self.lbl_welcome.grid(row=0, columnspan=2, sticky="news", pady=10)
        
        self.lbl_language = tk.Label(self.model_frame, text = 'Select Language:', font= self.gui_font)
        self.lbl_language.grid(row=1, column=0, sticky="w")

        self.lbl_model = tk.Label(self.model_frame, text = 'Select Model:', font= self.gui_font)
        self.lbl_model.grid(row=1, column=1, sticky="w")

        self.combo_languages = ttk.Combobox(self.model_frame, value=(self.languages), state="readonly", font= self.gui_font)
        self.combo_languages.bind('<<ComboboxSelected>>', self.on_combo_language_select)
        self.combo_languages.grid(row=2, column=0, sticky="news", pady=2)
        self.combo_languages.current(0)
        
        model_name = self.get_model(self.combo_languages.get())
        self.combo_models = ttk.Combobox(self.model_frame, values=model_name, state="readonly", font= self.gui_font)
        self.combo_models.bind('<<ComboboxSelected>>', self.on_combo_model_select)
        self.combo_models.grid(row=2, column=1, sticky="news", pady=2)
        self.combo_models.current(0)
        self.model_to_download = self.combo_models.get()

        self.lbl_info = tk.Label(self.model_frame, text = 'Some info about the selected model.. ', font= self.gui_font)
        self.lbl_info.grid(row=3, columnspan=2, sticky="w", pady=10)
        
        size, error, notes, license = self.get_model_info(self.combo_models.get(),self.combo_languages.get())
        model_info = "Name: %s\nSize: %s\nWord error rate/Speed: %s\nNotes: %s\nLicense: %s\n" % (self.model_to_download, size, error, notes, license)
        self.model_info_message = tk.Message(self.model_frame, width=(self.gui_x-5), text= model_info, background='white', font=self.gui_font)
        self.model_info_message.grid(row=4, columnspan=2, sticky="news", pady=2)

        self.directory_frame.grid_rowconfigure(3, weight=1)
        self.directory_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_download = tk.Label(self.directory_frame, text= "Download model in directory: ", font= self.gui_font, anchor=tk.W)
        self.lbl_download.grid(row=0, column=0, sticky="w", pady=10)
        
        self.lbl_directory = tk.Label(self.directory_frame, text= self.model_dir, font= self.gui_font, anchor=tk.W)
        self.lbl_directory.grid(row=1, column=0, sticky="news")
        
        self.btn_browse = tk.Button(self.directory_frame, text = "Browse", width=10, command=lambda:self.btn_click_browse_folder(), font = self.gui_font)
        self.btn_browse.grid(row=1, column=1, sticky="news", pady=10)
        
        self.btn_download = tk.Button(self.directory_frame, text = "Download!", width=10, command=lambda:self.btn_click_download(self.model_to_download), font = self.gui_font)
        self.btn_download.grid(row=2, column=1, sticky="news",pady=10)
        
        self.progressbar = ttk.Progressbar(self.directory_frame, length=400)
        self.progressbar.grid(row=2, column=0,  sticky="news", pady=10)
        
    def get_listbox_language(self):
        value = self.listbox_languages.get(tk.ANCHOR)
    
    def get_listbox_model(self):
        value = self.listbox_model.get(tk.ANCHOR)     

    def btn_click_browse_folder(self):
        path = filedialog.askdirectory()
        if len(path) != 0:
            self.model_dir = path
            self.lbl_directory.config(text= self.model_dir)

    def get_model(self, language):
        models = []
        for model in self.model_names:
            if model["Language"] == language:
                models.append(model['Model'])
        return(models)
        
    def load_models(self):
        http = urllib3.PoolManager()

        self.url = "https://alphacephei.com/vosk/models"
        
        self.r = http.request('GET', self.url)
        soup = BeautifulSoup(self.r.data, 'html.parser')
        
        head_list = []
        item_list = []
        model_list = []
        language_list = []
        language = None
        
        for table in soup.find_all('table'):
            for head in table.find_all('thead'):
                for column in head.find_all('th'):
                    head_list.append(column.text)
            for table_body in table.find_all('tbody'):
                for row in table_body.find_all('tr'):
                    row_list = []
                    for column in row.find_all('td'):
                        row_list.append(column.text)
                    item_list.append(row_list)
            break

        for item in item_list:
            if len(item) == 5:
                if item[0] != "\xa0" and item[1] == "\xa0" and (item[2] == "\xa0" or item[2] == "Older Models") and item[3] == "\xa0":
                    language = item[0]
                    if language_list.count(language) == 0:
                        language_list.append(language)
                else:
                    model_dict = {"Language": language, head_list[0]: item[0], head_list[1]: item[1], head_list[2]: item[2], head_list[3]: item[3], head_list[4]: item[4]}    
                    model_list.append(model_dict)
        return language_list, model_list

    def get_model_info(self, selected_model, language):
        size = None 
        error = None 
        notes = None
        license = None
        for model in self.model_names:
            if model["Language"] == language:
                if model["Model"] == selected_model:
                    size = model["Size"]
                    error = model["Word error rate/Speed"]
                    notes = model["Notes"]
                    license = model["License"]
                    break
        return size, error, notes, license

    def btn_click_download(self, model_to_download):
        downloadThread= Thread(target=lambda:self.download(model_to_download))
        downloadThread.start()
        self.btn_download["state"] = "disabled"
        self.btn_browse["state"] = "disabled"
    
    def download(self, model_to_download):
        model_url, filename = self.get_model_link(model_to_download)
        
        if model_url!=None:
            req=requests.get(model_url,stream=True)

            if "Content-Length" in req.headers:
                total_size=req.headers['Content-Length']
            else:
                total_size=None
            with open(self.model_dir+filename,"wb") as fileobj:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        fileobj.write(chunk)
                        current_size=os.path.getsize(self.model_dir+filename)
                        #lbl_size.config(text=str(getStandardSize(current_size)))
    
                        if total_size!=None:
                            percentage = round((int(current_size)/int(total_size))*100)
                            #lbl_percentage.config(text=str(percentg)+" %")
                            self.progressbar['value']=percentage
                        else:
                            percentage = "Infinite"
                            self.progressbar.config(mode="indeterminate")
                            self.progressbar.start()
                            #labelPercentage.config(text=str(percentage)+" %")
    
            if total_size!=None:
                current_size=os.path.getsize(self.model_dir+filename)
                #lbl_size.config(text=str(getStandardSize(current_size)))
                #lbl_percentage.config(text=str(percentage) + " %")
                percentage=round((int(current_size)/int(total_size))*100)
                self.progressbar['value']=percentage
                self.btn_download["state"] = "normal"
                self.btn_browse["state"] = "normal"
                
                self.unzip(self.model_dir, filename)

                if self.execution_method == "inner":
                    self.gui_master.destroy()
                    #quit
            else:
                current_size=os.path.getsize(self.model_dir+filename)
                #lbl_size.config(text=str(getStandardSize(current_size)))
                #lbl_percentage.config(text="100 %")
                self.progressbar['value'] = 100
                self.btn_download["state"] = "normal"
                self.btn_browse["state"] = "normal"

    def on_combo_language_select(self, event):
        self.combo_models.set("")
        model = self.get_model(self.combo_languages.get())
        self.combo_models.config(values = model)
        self.combo_models.current(0)
        
        self.model_to_download = self.combo_models.get()
        selected_language = self.combo_languages.get()
        size, error, notes, license = self.get_model_info(self.model_to_download, selected_language)
        info = "Name: %s\nSize: %s\nWord error rate/Speed: %s\nNotes: %s\nLicense: %s\n" % (self.model_to_download, size, error, notes, license)
        self.model_info_message.config(text=info)

    def get_model_link(self, model_to_download):
        soup = BeautifulSoup(self.r.data, "lxml")

        for link in soup.findAll('a'):
            model_link = link.get('href')
            if model_link.startswith(self.url):
                if model_to_download+".zip" in model_link:
                    file_name = model_link.split(self.url+'/', 1)
                    file_name = file_name[1]
                    return model_link, file_name

    def on_combo_model_select(self, event):
        self.model_to_download = self.combo_models.get()
        selected_language = self.combo_languages.get()
        size, error, notes, license = self.get_model_info(self.model_to_download, selected_language)
        info = "Name: %s\nSize: %s\nWord error rate/Speed: %s\nNotes: %s\nLicense: %s\n" % (self.model_to_download, size, error, notes, license)
        self.model_info_message.config(text=info)
    
    def unzip(self, directory, filename):
        with zipfile.ZipFile(directory+filename, 'r') as zip_ref:
                zip_ref.extractall(directory)
        os.remove(directory+filename)

    def execute_standalone(self):
        self.execution_method = "standalone"
        self.gui_master.mainloop()
        
    def execute(self):            
        self.execution_method = "inner"
        self.gui_master.mainloop()

if __name__ == '__main__':
    downloader = model_downloader()
    downloader.execute_standalone()