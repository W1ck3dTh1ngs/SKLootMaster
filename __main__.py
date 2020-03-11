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
            return resp.content
        return resp


###############################################################################
# Trello Data Parse Class
class Trello_Data:
    def __init__(self):
        self.all_lists = Trello("GET",
                                f"/1/boards/{config['trello']['board_id']}"
                                f"/lists",
                                auth,
                                None).get_response().json()
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
                                    None).get_response().json()
        except Exception as e:
            print(e)
        del batch_params["urls"]
        return batch_response


###############################################################################
# Collect and organize the initial Trello data
current_data = Trello_Data()
sk_tracker = []


###############################################################################
# Buttons / Functions
def class_color(card):
    if card["labels"][0]["name"] == "Warrior":
        color = config["colors"]["warrior"]
    elif card["labels"][0]["name"] == "Druid":
        color = config["colors"]["druid"]
    elif card["labels"][0]["name"] == "Hunter":
        color = config["colors"]["hunter"]
    elif card["labels"][0]["name"] == "Mage":
        color = config["colors"]["mage"]
    elif card["labels"][0]["name"] == "Priest":
        color = config["colors"]["priest"]
    elif card["labels"][0]["name"] == "Rogue":
        color = config["colors"]["rogue"]
    elif card["labels"][0]["name"] == "Shaman":
        color = config["colors"]["shaman"]
    elif card["labels"][0]["name"] == "Warlock":
        color = config["colors"]["warlock"]
    return color


def refresh_tklists():
    print("Refreshing lists...")
    main_list.delete(0, "end")
    tier_list.delete(0, "end")
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
    for card in current_data.members:
        global_list.insert("end",
                           f"{card['name']} - ({card['labels'][0]['name']})")
        global_list.itemconfig("end", {"fg": config["colors"]["text"],
                                       "bg": class_color(card)})
    try:
        for card in current_data.main_live_cards:
            if card["labels"][0]["name"].lower() in active_filters:
                main_list.insert("end",
                                 f"{card['name']} - "
                                 f"({card['labels'][0]['name']})")
                main_list.itemconfig("end", {"fg": config["colors"]["text"],
                                             "bg": class_color(card)})
            main_count += 1
        for card in current_data.tier_live_cards:
            if card["labels"][0]["name"].lower() in active_filters:
                tier_list.insert("end",
                                 f"{card['name']} - "
                                 f"({card['labels'][0]['name']})")
                tier_list.itemconfig("end", {"fg": config["colors"]["text"],
                                             "bg": class_color(card)})
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
    return True


def check_lists():
    try:
        if (current_data.main_live_id and
                current_data.main_pull_id and
                current_data.tier_live_id and
                current_data.tier_pull_id):
            return True
    except AttributeError:
        return False


def create_lists():
    global current_data
    current_data = Trello_Data()
    qparams = auth
    if check_lists():
        log_list.insert("end",
                        "A pull/live list already exists.")
        return False
    qparams["idBoard"] = config['trello']['board_id']
    qparams["name"] = config["trello"]["main_pull"]
    qparams["idListSource"] = current_data.main_master_id
    qparams["pos"] = "bottom"
    print("Creating main pull list...")
    resp1 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).get_response()
    qparams["name"] = config["trello"]["tier_pull"]
    qparams["idListSource"] = current_data.tier_master_id
    qparams["pos"] = "bottom"
    print("Creating tier pull list...")
    resp2 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).get_response()
    del qparams["idListSource"]
    qparams["name"] = config["trello"]["main_live"]
    qparams["pos"] = "bottom"
    print("Creating main live list...")
    resp3 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).get_response()
    qparams["name"] = config["trello"]["tier_live"]
    qparams["pos"] = "bottom"
    print("Creating tier live list...")
    resp4 = Trello("POST",
                   "/1/lists",
                   qparams,
                   None).get_response()
    del qparams["idBoard"], qparams["name"], qparams["pos"]
    current_data = Trello_Data()
    refresh_tklists()
    print("Done creating pull/live.")
    return True


def add_to_raid():
    global current_data
    current_data = Trello_Data()
    if not check_lists():
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth
    for name in chosen_player("Extended"):
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
                               None).get_response()
                qparams["idList"] = current_data.tier_live_id
                qparams["idCardSource"] = tier_card_id
                qparams["pos"] = tier_pos
                resp2 = Trello("POST",
                               "/1/cards",
                               qparams,
                               None).get_response()
                del qparams["idList"], qparams["idCardSource"], qparams["pos"]
                qparams["name"] = "-"
                resp3 = Trello("PUT",
                               f"/1/cards/{main_card_id}",
                               qparams,
                               None).get_response()
                resp4 = Trello("PUT",
                               f"/1/cards/{tier_card_id}",
                               qparams,
                               None).get_response()
                del qparams["name"], main_card_id, tier_card_id
                print("Finished adding.")
                log_list.insert("end",
                                f"{name} added to live lists.")
        except NameError:
            print(f"Unable to add {name}. May have already been added.")
            log_list.insert("end",
                            f"Unable to add {name}.")
            continue
    current_data = Trello_Data()
    refresh_tklists()
    return True


def remove_from_raid():
    global current_data
    current_data = Trello_Data()
    if not check_lists():
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth
    for name in chosen_player("Extended"):
        print(f"Removing {name} from live lists...")
        main_count = 0
        tier_count = 0
        main_pull_count = 0
        tier_pull_count = 0
        try:
            for card in current_data.main_live_cards:
                main_count += 1
                if card["name"] == name:
                    main_live_card_id = card["id"]
                    break
            for card in current_data.tier_live_cards:
                tier_count += 1
                if card["name"] == name:
                    tier_live_card_id = card["id"]
                    break
            for card in current_data.main_pull_cards:
                if card["name"] == "-":
                    main_pull_count += 1
                if main_pull_count == main_count:
                    main_pull_card_id = card["id"]
                    main_pull_pos = card["pos"]
                    break
            for card in current_data.tier_pull_cards:
                if card["name"] == "-":
                    tier_pull_count += 1
                if tier_pull_count == tier_count:
                    tier_pull_card_id = card["id"]
                    tier_pull_pos = card["pos"]
                    break
            if main_live_card_id and tier_live_card_id:
                qparams["idList"] = current_data.main_pull_id
                qparams["pos"] = main_pull_pos
                resp1 = Trello("PUT",
                               f"/1/cards/{main_live_card_id}",
                               qparams,
                               None).get_response()
                qparams["idList"] = current_data.tier_pull_id
                qparams["pos"] = tier_pull_pos
                resp2 = Trello("PUT",
                               f"/1/cards/{tier_live_card_id}",
                               qparams,
                               None).get_response()
                del qparams["idList"], qparams["pos"]
                resp3 = Trello("DELETE",
                               f"/1/cards/{main_pull_card_id}",
                               qparams,
                               None).get_response()
                resp4 = Trello("DELETE",
                               f"/1/cards/{tier_pull_card_id}",
                               qparams,
                               None).get_response()
                del main_live_card_id, tier_live_card_id
                print("Finished removing.")
                log_list.insert("end",
                                f"{name} removed from live lists.")
        except NameError:
            print(f"Unable to remove {name}. May have already been removed.")
            log_list.insert("end",
                            f"Unable to remove {name}.")
            continue
    current_data = Trello_Data()
    refresh_tklists()
    return True


def mainsk():
    global current_data
    if chosen_player("Single") is not False:
        suicide(chosen_player("Single"), "Main")
    else:
        return False
    current_data = Trello_Data()
    refresh_tklists()
    return True


def tiersk():
    global current_data
    if chosen_player("Single") is not False:
        suicide(chosen_player("Single"), "Tier")
    current_data = Trello_Data()
    refresh_tklists()
    return True


def chosen_player(limit_type):
    if limit_type == "Single":
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
                            "Requires  1 selection.")
            return False
        name = slist.get(selection)[:slist.get(selection).index(" ")]
        return name
    elif limit_type == "Extended":
        names = []
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
                for label in selection:
                    names.append(slist.get(label)
                                 [:slist.get(label).index(" ")])
                return names
        except UnboundLocalError:
            log_list.insert("end",
                            "No player selected.")
            return False


def suicide(name, sklist):
    if not check_lists():
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    qparams = auth
    if sklist == "Main":
        for card in current_data.main_live_cards:
            if card["name"] == name:
                sk_data = {}
                sk_data["name"] = name
                sk_data["main_id"] = card["id"]
                sk_data["main_pos"] = card["pos"]
                qparams["pos"] = "bottom"
                resp1 = Trello("PUT",
                               f"/1/cards/{sk_data['main_id']}",
                               qparams,
                               None).get_response()
                break
        for card in current_data.tier_live_cards:
            if card["name"] == name:
                sk_data["tier_id"] = card["id"]
                sk_data["tier_pos"] = card["pos"]
                resp2 = Trello("PUT",
                               f"/1/cards/{sk_data['tier_id']}",
                               qparams,
                               None).get_response()
                break
        del qparams["pos"]
        sk_tracker.append(sk_data)
        print(f"{name} used Main SK.")
        log_list.insert("end",
                        f"{name} used Main SK.")
        return True
    if sklist == "Tier":
        for card in current_data.main_live_cards:
            if card["name"] == name:
                sk_data = {}
                sk_data["name"] = name
                sk_data["main_id"] = card["id"]
                sk_data["main_pos"] = card["pos"]
                break
        for card in current_data.tier_live_cards:
            if card["name"] == name:
                sk_data["tier_id"] = card["id"]
                sk_data["tier_pos"] = card["pos"]
                qparams["pos"] = "bottom"
                resp1 = Trello("PUT",
                               f"/1/cards/{sk_data['tier_id']}",
                               qparams,
                               None).get_response()
                break
        del qparams["pos"]
        sk_tracker.append(sk_data)
        print(f"{name} used Tier SK.")
        log_list.insert("end",
                        f"{name} used Tier SK.")
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
                   None).get_response()
    qparams["pos"] = sk_tracker[-1]["tier_pos"]
    resp2 = Trello("PUT",
                   f"/1/cards/{sk_tracker[-1]['tier_id']}",
                   qparams,
                   None).get_response()
    del qparams["pos"]
    log_list.insert("end",
                    f"SK undone: {sk_tracker[-1]['name']}")
    sk_tracker.pop(-1)
    current_data = Trello_Data()
    refresh_tklists()
    return True


def merge_lists():
    global current_data
    if not check_lists():
        log_list.insert("end",
                        "Missing pull/live lists.")
        return False
    print("Merging Live lists into Pull lists...\n"
          "This can take a while...")
    qparams = auth
    try:
        i = 0
        while len(current_data.main_live_cards) > 0:
            if current_data.main_pull_cards[i]["name"] == "-":
                main_live_card_id = current_data.main_live_cards[0]["id"]
                main_pull_card_id = current_data.main_pull_cards[i]["id"]
                qparams["idList"] = current_data.main_pull_id
                qparams["pos"] = current_data.main_pull_cards[i]["pos"]
                print("Main merging "
                      f"{current_data.main_live_cards[0]['name']}")
                resp1 = Trello("PUT",
                               f"/1/cards/{main_live_card_id}",
                               qparams,
                               None).get_response()
                del qparams["idList"], qparams["pos"]
                resp2 = Trello("DELETE",
                               f"/1/cards/{main_pull_card_id}",
                               qparams,
                               None).get_response()
                current_data = Trello_Data()
            i += 1
    except AttributeError as e:
        pass
    try:
        i = 0
        while len(current_data.tier_live_cards) > 0:
            if current_data.tier_pull_cards[i]["name"] == "-":
                tier_live_card_id = current_data.tier_live_cards[0]["id"]
                tier_pull_card_id = current_data.tier_pull_cards[i]["id"]
                qparams["idList"] = current_data.tier_pull_id
                qparams["pos"] = current_data.tier_pull_cards[i]["pos"]
                print("Tier merging "
                      f"{current_data.tier_live_cards[0]['name']}")
                resp3 = Trello("PUT",
                               f"/1/cards/{tier_live_card_id}",
                               qparams,
                               None).get_response()
                del qparams["idList"], qparams["pos"]
                resp4 = Trello("DELETE",
                               f"/1/cards/{tier_pull_card_id}",
                               qparams,
                               None).get_response()
                current_data = Trello_Data()
            i += 1
    except AttributeError as e:
        pass
    qparams["value"] = 1
    try:
        resp5 = Trello("PUT",
                       f"/1/lists/{current_data.main_live_id}/closed",
                       qparams,
                       None).get_response()
    except AttributeError:
        pass
    try:
        resp6 = Trello("PUT",
                       f"/1/lists/{current_data.tier_live_id}/closed",
                       qparams,
                       None).get_response()
    except AttributeError:
        pass
    del qparams["value"]
    print("Merge complete.")
    log_list.insert("end",
                    "Live merged to pull.")
    refresh_tklists()
    return True


###############################################################################
# Configure tkinter window
window = Tk()
window.geometry("680x1000")
window.config(bg="#202533")
window.title("Whiteclaw Clan Loot Master")
canvas = Canvas(window, bg="#202533", width=100, height=100)
img = PhotoImage(file="logo100x100.gif")
canvas.create_image(50, 50, anchor="center", image=img)

# Global Frame
global_label = Label(window, bg="#202533", fg="#ffffff",
                     text="Global List  |  Log  |  Controls")
global_frame = Frame(window, bg="#202533", borderwidth=5,
                     relief="sunken")
global_list = Listbox(global_frame, bg="#202533", fg="#ffffff",
                      font=("Helvetica", 12),
                      height=20, width=25, selectmode="extended",
                      highlightcolor="#D94A66",
                      highlightthickness="3",
                      selectbackground="#D94A66")
gl_scrollbar = Scrollbar(global_frame, orient="vertical")
gl_scrollbar.config(command=global_list.yview, bg="#2c3b47")
global_list.config(yscrollcommand=gl_scrollbar.set)
log_list = Listbox(global_frame, bg="#202533", fg="#ffffff",
                   font=("Helvetica", 12), height=20, width=25,
                   highlightcolor="#D94A66",
                   highlightthickness="3",
                   selectbackground="#D94A66")
ll_scrollbar = Scrollbar(global_frame, orient="vertical")
ll_scrollbar.config(command=log_list.yview, bg="#2c3b47")
log_list.config(yscrollcommand=ll_scrollbar.set)

# Live Lists Frame
local_label = Label(window, bg="#202533", fg="#ffffff",
                    text=(f"{config['trello']['main_live']}  |  "
                          f"{config['trello']['tier_live']}  |  Filters"))
main_frame = Frame(window, bg="#202533", borderwidth=5, relief="raised")
main_list = Listbox(main_frame, bg="#202533", fg="#ffffff",
                    font=("Helvetica", 12), height=20, width=25,
                    highlightcolor="#D94A66",
                    highlightthickness="3",
                    selectbackground="#D94A66")
ml_scrollbar = Scrollbar(main_frame, orient="vertical")
ml_scrollbar.config(command=main_list.yview, bg="#2c3b47")
main_list.config(yscrollcommand=ml_scrollbar.set)
tier_list = Listbox(main_frame, bg="#202533", fg="#ffffff",
                    font=("Helvetica", 12), height=20, width=25,
                    highlightcolor="#D94A66",
                    highlightthickness="3",
                    selectbackground="#D94A66")
tl_scrollbar = Scrollbar(main_frame, orient="vertical")
tl_scrollbar.config(command=main_list.yview, bg="#2c3b47")
tier_list.config(yscrollcommand=tl_scrollbar.set)
create_pl_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                          command=create_lists,
                          text="Create pull/live lists", width=25)
add_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                    command=add_to_raid,
                    text="Add player", width=25)
remove_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                       command=remove_from_raid,
                       text="Remove player", width=25)
mainsk_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                       command=mainsk,
                       text="Main SK", width=25)
tiersk_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                       command=tiersk,
                       text="Tier SK", width=25)
undo_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                     command=undosk,
                     text="Undo SK", width=25)
merge_button = Button(global_frame, bg="#2c3b47", fg="#ffffff",
                      command=merge_lists,
                      text="Merge lists", width=25)
filters = {"druid": IntVar(), "hunter": IntVar(), "mage": IntVar(),
           "priest": IntVar(), "rogue": IntVar(), "shaman": IntVar(),
           "warlock": IntVar(), "warrior": IntVar()}
druid_filter = Checkbutton(main_frame, text="Druid",
                           variable=filters["druid"],
                           bg=config["colors"]["druid"], fg="#000000",
                           font=("Helvetica", 12),
                           height=1, width=15, anchor="w",
                           highlightcolor="#D94A66")
hunter_filter = Checkbutton(main_frame, text="Hunter",
                            variable=filters["hunter"],
                            bg=config["colors"]["hunter"], fg="#000000",
                            font=("Helvetica", 12),
                            height=1, width=15, anchor="w",
                            highlightcolor="#D94A66")
mage_filter = Checkbutton(main_frame, text="Mage",
                          variable=filters["mage"],
                          bg=config["colors"]["mage"], fg="#000000",
                          font=("Helvetica", 12),
                          height=1, width=15, anchor="w",
                          highlightcolor="#D94A66")
priest_filter = Checkbutton(main_frame, text="Priest",
                            variable=filters["priest"],
                            bg=config["colors"]["priest"], fg="#000000",
                            font=("Helvetica", 12),
                            height=1, width=15, anchor="w",
                            highlightcolor="#D94A66")
rogue_filter = Checkbutton(main_frame, text="Rogue",
                           variable=filters["rogue"],
                           bg=config["colors"]["rogue"], fg="#000000",
                           font=("Helvetica", 12),
                           height=1, width=15, anchor="w",
                           highlightcolor="#D94A66")
shaman_filter = Checkbutton(main_frame, text="Shaman",
                            variable=filters["shaman"],
                            bg=config["colors"]["shaman"], fg="#000000",
                            font=("Helvetica", 12),
                            height=1, width=15, anchor="w",
                            highlightcolor="#D94A66")
warlock_filter = Checkbutton(main_frame, text="Warlock",
                             variable=filters["warlock"],
                             bg=config["colors"]["warlock"], fg="#000000",
                             font=("Helvetica", 12),
                             height=1, width=15, anchor="w",
                             highlightcolor="#D94A66")
warrior_filter = Checkbutton(main_frame, text="Warrior",
                             variable=filters["warrior"],
                             bg=config["colors"]["warrior"], fg="#000000",
                             font=("Helvetica", 12),
                             height=1, width=15, anchor="w",
                             highlightcolor="#D94A66")
apply_filters = Button(main_frame, bg="#2c3b47", fg="#ffffff",
                       command=refresh_tklists,
                       text="Filter/Refresh", width=25)
main_count_label = Label(main_frame, bg="#202533", fg="#ffffff",
                         text=f"{config['trello']['main_live']}: 0")
tier_count_label = Label(main_frame, bg="#202533", fg="#ffffff",
                         text=f"{config['trello']['tier_live']}: 0")

# Global List Frame
canvas.pack()
global_label.pack()
global_frame.pack()
global_list.pack(fill="y", side="left")
gl_scrollbar.pack(fill="y", side="left")
log_list.pack(side="left", fill="y")
ll_scrollbar.pack(side="left", fill="y")
create_pl_button.pack(pady=5)
add_button.pack(pady=5)
remove_button.pack(pady=5)
mainsk_button.pack(pady=5)
tiersk_button.pack(pady=5)
undo_button.pack(pady=5)
merge_button.pack(pady=5)

# Live Lists Frame
local_label.pack()
main_frame.pack()
main_list.pack(side="left", fill="y")
ml_scrollbar.pack(side="left", fill="y")
tier_list.pack(side="left", fill="y")
tl_scrollbar.pack(side="left", fill="y")
druid_filter.pack(side="top")
hunter_filter.pack(side="top")
mage_filter.pack(side="top")
priest_filter.pack(side="top")
rogue_filter.pack(side="top")
shaman_filter.pack(side="top")
warlock_filter.pack(side="top")
warrior_filter.pack(side="top")
apply_filters.pack(pady=5)
main_count_label.pack()
tier_count_label.pack()


###############################################################################
# Main logic
def main():
    refresh_tklists()
    window.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
