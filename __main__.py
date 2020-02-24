#!/usr/bin/env python3

import configparser
import os
import requests
from tkinter import *


###############################################################################
# Parse configuration file
fn = os.path.join(os.path.dirname(__file__), "config.txt")
config = configparser.ConfigParser()
config.read(fn)

# Set json for key and token to be used with query params
auth = {"key": config["auth"]["key"],
        "token": config["auth"]["secret"]}


###############################################################################
# Trello API Class
class Trello:
    def __init__(self, method, request, params, payload):
        self.base_url = "https://api.trello.com"
        self.headers = {"Content-Type": "application/json",
                        "accept": "application/json"}
        self.method = method
        self.request = request
        self.params = params
        self.payload = payload
        self.response = self.get_response()

    # Sends request and returns the response
    def get_response(self):
        url = f"{self.base_url}{self.request}"
        resp = requests.request(self.method,
                                url,
                                headers=self.headers,
                                params=self.params,
                                json=self.payload)
        if resp.status_code is not 200:
            print(f"API request failed with status: {resp.status_code}")
        return resp


###############################################################################
# Trello Data Parse Class
class Trello_Data:
    def __init__(self):
        self.all_lists = self.get_lists()
        self.all_cards = self.batch_get_cards(self.all_lists)
        for list in self.all_lists:
            try:
                if list["name"] == config["trello"]["main_master"]:
                    self.main_master_id = list["id"]
                    continue
                elif list["name"] == config["trello"]["tier_master"]:
                    self.tier_master_id = list["id"]
                    continue
                elif list["name"] == config["trello"]["main_pull"]:
                    self.main_pull_id = list["id"]
                    continue
                elif list["name"] == config["trello"]["tier_pull"]:
                    self.tier_pull_id = list["id"]
                    continue
                elif list["name"] == config["trello"]["main_live"]:
                    self.main_live_id = list["id"]
                    continue
                elif list["name"] == config["trello"]["tier_live"]:
                    self.tier_live_id = list["id"]
            except IndexError:
                continue
            except AttributeError:
                pass
            except TypeError as e:
                print(e)
        for response in self.all_cards:
            try:
                if response["200"][0]["idList"] == self.main_master_id:
                    self.main_master_cards = response["200"]
                    continue
                elif response["200"][0]["idList"] == self.tier_master_id:
                    self.tier_master_cards = response["200"]
                    continue
                elif response["200"][0]["idList"] == self.main_pull_id:
                    self.main_pull_cards = response["200"]
                    continue
                elif response["200"][0]["idList"] == self.tier_pull_id:
                    self.tier_pull_cards = response["200"]
                    continue
                elif response["200"][0]["idList"] == self.main_live_id:
                    self.main_live_cards = response["200"]
                    continue
                elif response["200"][0]["idList"] == self.tier_live_id:
                    self.tier_live_cards = response["200"]
            except IndexError:
                continue
            except AttributeError:
                pass
            except TypeError as e:
                print(e)
        self.members = sorted(self.main_master_cards,
                              key=lambda i: (i['name']))

    def batch_get_cards(self, lists):
        batch_urls = []
        for list in lists:
            batch_urls.append(f"/lists/{list['id']}/cards")
        batch_params = auth
        batch_params["urls"] = batch_urls
        try:
            batch_response = Trello("GET",
                                    f"/1/batch",
                                    batch_params,
                                    None).response.json()
        except Exception as e:
            print(e)
        del batch_params["urls"]
        return batch_response

    def get_lists(self):
        try:
            all_lists = Trello("GET",
                               f"/1/boards/{config['trello']['board_id']}"
                               f"/lists",
                               auth,
                               None).response.json()
        except Exception as e:
            print(e)
        return all_lists


###############################################################################
# Collect and organize the initial Trello data
current_data = Trello_Data()

# Configure tkinter window
window = Tk()
window.geometry("680x1000")
window.config(bg="#202533")
window.title("Whiteclaw Clan Loot Master")
canvas = Canvas(window, bg="#202533", width=100, height=100)
canvas.pack()
img = PhotoImage(file="logo100x100.gif")
canvas.create_image(50, 50, anchor="center", image=img)

# Global Frame
Label(window, bg="#202533", fg="#ffffff",
      text="Global List  |  Log  |  Controls").pack()
global_frame = Frame(window, bg="#202533", borderwidth=5,
                     relief="sunken")
global_frame.pack()
global_list = Listbox(global_frame, bg="#202533", fg="#ffffff",
                      font=("Helvetica", 12),
                      height=20, width=25, selectmode="extended")
global_list.pack(fill="y", side="left")
gl_scrollbar = Scrollbar(global_frame, orient="vertical")
gl_scrollbar.config(command=global_list.yview)
gl_scrollbar.pack(fill="y", side="left")
global_list.config(yscrollcommand=gl_scrollbar.set)
log_list = Listbox(global_frame, bg="#202533", fg="#ffffff",
                   font=("Helvetica", 12), height=20, width=25)
log_list.pack(side="left", fill="y")
ll_scrollbar = Scrollbar(global_frame, orient="vertical")
ll_scrollbar.config(command=log_list.yview)
ll_scrollbar.pack(side="left", fill="y")
log_list.config(yscrollcommand=ll_scrollbar.set)
sk_tracker = []


###############################################################################
# Buttons / Functions

def class_color(card):
    if card['labels'][0]['name'] == "Warrior":
        color = "#331a00"
    elif card['labels'][0]['name'] == "Druid":
        color = "#803300"
    elif card['labels'][0]['name'] == "Hunter":
        color = "#003300"
    elif card['labels'][0]['name'] == "Mage":
        color = "#006666"
    elif card['labels'][0]['name'] == "Priest":
        color = "#404040"
    elif card['labels'][0]['name'] == "Rogue":
        color = "#666600"
    elif card['labels'][0]['name'] == "Shaman":
        color = "#000066"
    elif card['labels'][0]['name'] == "Warlock":
        color = "#330033"
    return color


def refresh_tklists():
    print("Refreshing lists...")
    main_list.delete(0, 'end')
    tier_list.delete(0, 'end')
    active_filters = []
    for key, value in filters.items():
        if value.get() == 1:
            active_filters.append(key)
    if len(active_filters) == 0:
        active_filters = ["druid", "hunter", "mage",
                          "priest", "rogue", "shaman",
                          "warlock", "warrior"]
    main_count = 0
    tier_count = 0
    try:
        for card in current_data.main_live_cards:
            if card["labels"][0]["name"].lower() in active_filters:
                main_list.insert("end",
                                 f"{card['name']} - "
                                 f"({card['labels'][0]['name']})")
                main_list.itemconfig("end", {"bg": class_color(card)})
            main_count += 1
    except AttributeError:
        pass
    try:
        for card in current_data.tier_live_cards:
            if card["labels"][0]["name"].lower() in active_filters:
                tier_list.insert("end",
                                 f"{card['name']} - "
                                 f"({card['labels'][0]['name']})")
                tier_list.itemconfig("end", {"bg": class_color(card)})
            tier_count += 1
    except AttributeError:
        pass
    if main_count != tier_count:
        print("WARNING: Asymmetrical counts between main and tier lists.")
        main_count_label.config(fg="red")
        tier_count_label.config(fg="red")
    main_count_label.config(text=(f"{config['trello']['main_live']}: "
                                  f"{main_count}"))
    tier_count_label.config(text=(f"{config['trello']['tier_live']}: "
                                  f"{tier_count}"))
    print("Done refreshing.")
    return main_count, tier_count


def create_lists():
    global current_data
    qparams = auth
    try:
        if (current_data.main_live_id or
                current_data.main_pull_id or
                current_data.tier_live_id or
                current_data.tier_pull_id):
            log_list.insert("end",
                            "A pull/live list already exists.")
            return False
    except AttributeError:
        pass
    qparams["idBoard"] = config['trello']['board_id']
    qparams["name"] = config["trello"]["main_pull"]
    qparams["idListSource"] = current_data.main_master_id
    qparams["pos"] = "bottom"
    print("Creating main pull list...")
    resp1 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None)
    qparams["name"] = config["trello"]["tier_pull"]
    qparams["idListSource"] = current_data.tier_master_id
    qparams["pos"] = "bottom"
    print("Creating tier pull list...")
    resp2 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None)
    del qparams["idListSource"]
    qparams["name"] = config["trello"]["main_live"]
    qparams["pos"] = "bottom"
    print("Creating main live list...")
    resp3 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).response
    qparams["name"] = config["trello"]["tier_live"]
    qparams["pos"] = "bottom"
    print("Creating tier live list...")
    resp4 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).response
    del qparams["idBoard"], qparams["name"], qparams["pos"]
    current_data = Trello_Data()
    refresh_tklists()
    print("Done creating.")
    return True


def add_to_raid():
    global current_data
    try:
        if (current_data.main_live_id and
                current_data.main_pull_id and
                current_data.tier_live_id and
                current_data.tier_pull_id):
            pass
    except AttributeError:
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth
    if len(global_list.curselection()) > 0:
        slist = global_list
        selection = global_list.curselection()
    elif len(main_list.curselection()) > 0:
        slist = main_list
        selection = main_list.curselection()
    elif len(tier_list.curselection()) > 0:
        slist = tier_list
        selection = tier_list.curselection()
    try:
        if selection:
            pass
    except UnboundLocalError:
        log_list.insert("end",
                        "No player selected.")
        return False
    for i in selection:
        name = slist.get(i)[:slist.get(i).index(" ")]
        print(f"Adding {name} to live lists...")
        try:
            for card in current_data.main_pull_cards:
                if card["name"] == name:
                    main_card_id = card["id"]
                    main_pos = card["pos"]
                    break
            for card in current_data.tier_pull_cards:
                if card["name"] == name:
                    tier_card_id = card["id"]
                    tier_pos = card["pos"]
                    break
            if main_card_id and tier_card_id:
                qparams["idList"] = current_data.main_live_id
                qparams["idCardSource"] = main_card_id
                qparams["pos"] = main_pos
                resp1 = Trello("POST",
                               "/1/cards",
                               qparams,
                               None)
                qparams["idList"] = current_data.tier_live_id
                qparams["idCardSource"] = tier_card_id
                qparams["pos"] = tier_pos
                resp2 = Trello("POST",
                               "/1/cards",
                               qparams,
                               None)
                del qparams["idList"], qparams["idCardSource"], qparams["pos"]
                print("Creating placeholders in pull lists...")
                qparams["name"] = "-"
                resp3 = Trello("PUT",
                               f"/1/cards/{main_card_id}",
                               qparams,
                               None)
                resp4 = Trello("PUT",
                               f"/1/cards/{tier_card_id}",
                               qparams,
                               None)
                del qparams["name"]
                print("Finished adding.")
                log_list.insert("end",
                                f"{name} added to live lists.")
        except AttributeError:
            log_list.insert("end",
                            "Pull lists don't exist. Create pull/live first.")
            break
        except NameError:
            print(f"Removing {name} from live lists...")
            for card in current_data.main_live_cards:
                if card["name"] == name:
                    main_live_card_id = card["id"]
                    main_live_pos = card["pos"]
                    break
            for card in current_data.tier_live_cards:
                if card["name"] == name:
                    tier_live_card_id = card["id"]
                    tier_live_pos = card["pos"]
                    break
            if main_live_card_id and tier_live_card_id:
                qparams["idList"] = current_data.main_pull_id
                qparams["pos"] = main_live_pos
                resp1 = Trello("PUT",
                               f"/1/cards/{main_live_card_id}",
                               qparams,
                               None)
                qparams["idList"] = current_data.tier_pull_id
                qparams["pos"] = tier_live_pos
                resp2 = Trello("PUT",
                               f"/1/cards/{tier_live_card_id}",
                               qparams,
                               None)
                del qparams["idList"], qparams["pos"]
                print("Cleaning up placeholder...")
                for card in current_data.main_pull_cards:
                    if (card["name"] == "-" and
                            card["pos"] == main_live_pos):
                        main_pull_card_id = card["id"]
                        break
                for card in current_data.tier_pull_cards:
                    if (card["name"] == "-" and
                            card["pos"] == tier_live_pos):
                        tier_pull_card_id = card["id"]
                        break
                resp3 = Trello("DELETE",
                               f"/1/cards/{main_pull_card_id}",
                               qparams,
                               None)
                resp4 = Trello("DELETE",
                               f"/1/cards/{tier_pull_card_id}",
                               qparams,
                               None)
                print("Finished removing.")
                log_list.insert("end",
                                f"{name} removed from live lists.")
    current_data = Trello_Data()
    refresh_tklists()
    return True


def mainsk():
    global current_data
    try:
        if (current_data.main_live_id and
                current_data.main_pull_id and
                current_data.tier_live_id and
                current_data.tier_pull_id):
            pass
    except AttributeError:
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth
    if len(global_list.curselection()) == 1:
        slist = global_list
        selection = global_list.curselection()
    elif len(main_list.curselection()) == 1:
        slist = main_list
        selection = main_list.curselection()
    elif len(tier_list.curselection()) == 1:
        slist = tier_list
        selection = tier_list.curselection()
    else:
        log_list.insert("end",
                        "Must have exactly one member selected to SK.")
        return False
    name = slist.get(selection)[:slist.get(selection).index(" ")]
    print(f"Main SK: {name}...")
    for card in current_data.main_live_cards:
        if card["name"] == name:
            sk_data = {}
            sk_data["name"] = name
            sk_data["main_id"] = card["id"]
            main_live_card_id = card["id"]
            sk_data["main_pos"] = card["pos"]
            qparams["pos"] = "bottom"
            resp1 = Trello("PUT",
                           f"/1/cards/{main_live_card_id}",
                           qparams,
                           None)
            del qparams["pos"]
            break
    for card in current_data.tier_live_cards:
        if card["name"] == name:
            sk_data["tier_id"] = card["id"]
            tier_live_card_id = card["id"]
            sk_data["tier_pos"] = card["pos"]
            qparams["pos"] = "bottom"
            resp2 = Trello("PUT",
                           f"/1/cards/{tier_live_card_id}",
                           qparams,
                           None)
            sk_tracker.append(sk_data)
            del qparams["pos"]
            break
    print("Finished Main SK.")
    log_list.insert("end",
                    f"{name} used Main SK.")
    current_data = Trello_Data()
    refresh_tklists()
    return True


def tiersk():
    global current_data
    try:
        if (current_data.main_live_id and
                current_data.main_pull_id and
                current_data.tier_live_id and
                current_data.tier_pull_id):
            pass
    except AttributeError:
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth

    if len(global_list.curselection()) == 1:
        slist = global_list
        selection = global_list.curselection()
    elif len(main_list.curselection()) == 1:
        slist = main_list
        selection = main_list.curselection()
    elif len(tier_list.curselection()) == 1:
        slist = tier_list
        selection = tier_list.curselection()
    else:
        log_list.insert("end",
                        "Must have exactly one member selected to SK.")
        return False
    name = slist.get(selection)[:slist.get(selection).index(" ")]
    print(f"Tier SK: {name}...")
    for card in current_data.tier_live_cards:
        if card["name"] == name:
            sk_data = {}
            sk_data["name"] = name
            sk_data["tier_id"] = card["id"]
            tier_live_card_id = card["id"]
            sk_data["tier_pos"] = card["pos"]
            qparams["pos"] = "bottom"
            resp1 = Trello("PUT",
                           f"/1/cards/{tier_live_card_id}",
                           qparams,
                           None)
            del qparams["pos"]
            break
    for card in current_data.main_live_cards:
        if card["name"] == name:
            sk_data["main_id"] = card["id"]
            sk_data["main_pos"] = card["pos"]
            sk_tracker.append(sk_data)
            break
    print("Finished Tier SK.")
    log_list.insert("end",
                    f"{name} used Tier SK.")
    current_data = Trello_Data()
    refresh_tklists()
    return True


def undosk():
    if len(sk_tracker) == 0:
        log_list.insert("end",
                        "No SK to undo.")
        return False
    global current_data
    qparams = auth
    qparams["pos"] = sk_tracker[-1]["main_pos"]
    print(f"Undo SK: {sk_tracker[-1]}")
    resp1 = Trello("PUT",
                   f"/1/cards/{sk_tracker[-1]['main_id']}",
                   qparams,
                   None)
    qparams["pos"] = sk_tracker[-1]["tier_pos"]
    resp2 = Trello("PUT",
                   f"/1/cards/{sk_tracker[-1]['tier_id']}",
                   qparams,
                   None)
    del qparams["pos"]
    log_list.insert("end",
                    f"SK undone: {sk_tracker[-1]['name']}")
    sk_tracker.pop(-1)
    current_data = Trello_Data()
    refresh_tklists()
    return True


def merge_lists():
    global current_data
    try:
        if (current_data.main_live_id and
                current_data.main_pull_id and
                current_data.tier_live_id and
                current_data.tier_pull_id):
            pass
    except AttributeError:
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    print("Merging Live lists into Pull lists...")
    qparams = auth
    i = 0
    try:
        while len(current_data.main_live_cards) > 0:
            if current_data.main_pull_cards[i]["name"] == "-":
                main_live_card_id = current_data.main_live_cards[0]["id"]
                main_pull_card_id = current_data.main_pull_cards[i]["id"]
                qparams["idList"] = current_data.main_pull_id
                qparams["pos"] = current_data.main_pull_cards[i]["pos"]
                resp1 = Trello("PUT",
                               f"/1/cards/{main_live_card_id}",
                               qparams,
                               None)
                del qparams["idList"], qparams["pos"]
                resp2 = Trello("DELETE",
                               f"/1/cards/{main_pull_card_id}",
                               qparams,
                               None)
                current_data = Trello_Data()
            i += 1
    except AttributeError as e:
        print(e)
    try:
        i = 0
        while len(current_data.tier_live_cards) > 0:
            if current_data.tier_pull_cards[i]["name"] == "-":
                tier_live_card_id = current_data.tier_live_cards[0]["id"]
                tier_pull_card_id = current_data.tier_pull_cards[i]["id"]
                qparams["idList"] = current_data.tier_pull_id
                qparams["pos"] = current_data.tier_pull_cards[i]["pos"]
                resp3 = Trello("PUT",
                               f"/1/cards/{tier_live_card_id}",
                               qparams,
                               None)
                del qparams["idList"], qparams["pos"]
                resp4 = Trello("DELETE",
                               f"/1/cards/{tier_pull_card_id}",
                               qparams,
                               None)
                current_data = Trello_Data()
            i += 1
    except AttributeError as e:
        print(e)
    qparams["value"] = 1
    try:
        resp5 = Trello("PUT",
                       f"/1/lists/{current_data.main_live_id}/closed",
                       qparams,
                       None)
    except AttributeError:
        pass
    try:
        resp6 = Trello("PUT",
                       f"/1/lists/{current_data.tier_live_id}/closed",
                       qparams,
                       None)
    except AttributeError:
        pass
    del qparams["value"]
    print("Merge done.")
    log_list.insert("end",
                    "Live merged to pull.")
    refresh_tklists()
    return True


create_pl_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                          command=create_lists,
                          text="Create pull/live lists", width=25)
create_pl_button.pack(pady=5)
add_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                    command=add_to_raid,
                    text="Add/Remove player", width=25)
add_button.pack(pady=5)
mainsk_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                       command=mainsk,
                       text="Main SK", width=25)
mainsk_button.pack(pady=5)
tiersk_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                       command=tiersk,
                       text="Tier SK", width=25)
tiersk_button.pack(pady=5)
undo_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                     command=undosk,
                     text="Undo SK", width=25)
undo_button.pack(pady=5)
merge_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                      command=merge_lists,
                      text="Merge lists", width=25)
merge_button.pack(pady=5)

###############################################################################
# Fill Global List
for card in current_data.members:
    global_list.insert("end",
                       f"{card['name']} - ({card['labels'][0]['name']})")
    global_list.itemconfig("end", {"bg": class_color(card)})

# Live Lists Frame
Label(window, bg="#202533", fg="#ffffff",
      text=(f"{config['trello']['main_live']}  |  "
            f"{config['trello']['tier_live']}  |  Filters")).pack()
main_frame = Frame(window, bg="#202533", borderwidth=5, relief="raised")
main_frame.pack()
main_list = Listbox(main_frame, bg="#202533", fg="#ffffff",
                    font=("Helvetica", 12), height=20, width=25)
main_list.pack(side="left", fill="y")
ml_scrollbar = Scrollbar(main_frame, orient="vertical")
ml_scrollbar.config(command=main_list.yview)
ml_scrollbar.pack(side="left", fill="y")
main_list.config(yscrollcommand=ml_scrollbar.set)
tier_list = Listbox(main_frame, bg="#202533", fg="#ffffff",
                    font=("Helvetica", 12), height=20, width=25)
tier_list.pack(side="left", fill="y")
tl_scrollbar = Scrollbar(main_frame, orient="vertical")
tl_scrollbar.config(command=main_list.yview)
tl_scrollbar.pack(side="left", fill="y")
tier_list.config(yscrollcommand=tl_scrollbar.set)
filters = {}
filters["druid"] = IntVar()
Checkbutton(main_frame, text="Druid", variable=filters["druid"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["hunter"] = IntVar()
Checkbutton(main_frame, text="Hunter", variable=filters["hunter"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["mage"] = IntVar()
Checkbutton(main_frame, text="Mage", variable=filters["mage"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["priest"] = IntVar()
Checkbutton(main_frame, text="Priest", variable=filters["priest"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["rogue"] = IntVar()
Checkbutton(main_frame, text="Rogue", variable=filters["rogue"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["shaman"] = IntVar()
Checkbutton(main_frame, text="Shaman", variable=filters["shaman"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["warlock"] = IntVar()
Checkbutton(main_frame, text="Warlock", variable=filters["warlock"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
filters["warrior"] = IntVar()
Checkbutton(main_frame, text="Warrior", variable=filters["warrior"],
            bg="#8585ad", fg="#000000",
            font=("Helvetica", 12),
            height=1, width=15, anchor="w").pack(side="top")
apply_filters = Button(main_frame, bg="#2c3b47", fg="#ffffff",
                       command=refresh_tklists,
                       text="Filter/Refresh", width=25)
apply_filters.pack(pady=5)
main_count_label = Label(main_frame, bg="#202533", fg="#ffffff",
                         text=f"{config['trello']['main_live']}: 0")
tier_count_label = Label(main_frame, bg="#202533", fg="#ffffff",
                         text=f"{config['trello']['tier_live']}: 0")
refresh_tklists()
main_count_label.pack()
tier_count_label.pack()


###############################################################################
# Main logic
def main():
    window.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
