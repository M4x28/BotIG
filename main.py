from instagrapi import Client
import os
import os.path
import time
from colorama import Fore
from dotenv import load_dotenv
import concurrent.futures


# Set Global ENV
load_dotenv()
MSG_COMMENT = os.getenv('MSG_COMMENT')
MSG_DIRECT = os.getenv('MSG_DIRECT')
DELAY = int(os.getenv('DELAY'))
N_MSG_PER_BOT = int(os.getenv('N_MSG_PER_BOT'))


def add_to_error(username, msg):
    with open('error.txt', 'a') as errorFile:
        errorFile.write(username + " " + msg + '\n')


def get_username_from_id(cl, id):
    try:
        return cl.username_from_user_id(id)
    except:
        print(Fore.RED + "Private Account, couldn't get username.")
        add_to_error(id, "Couldn't get username")


def get_user_id_from_username(cl, username):
    try:
        return cl.user_id_from_username(username)
    except:
        print(Fore.RED + "Private Account, couldn't get user id.")
        add_to_error(username, "Unable to get user id")


def comment_last_post(cl, user_id):
    try:
        media = cl.user_medias(user_id, 1)
    except:
        print(Fore.RED + "Private Account, couldn't find the last post.")
        add_to_error(get_username_from_id(user_id), "Unable to find the last post")
    else:
        media_id = media[0].id
        cl.media_comment(media_id, MSG_COMMENT)


def send_direct(cl, user_id):
    try:
        cl.direct_send(MSG_DIRECT, user_ids=[user_id])
    except:
        print("Error sending direct.")
        add_to_error(get_username_from_id(user_id), "Unable to send direct")


def add_to_done(username, comment):
    with open('done.txt', 'a') as doneFile:
        doneFile.write(username + ' ' + str(comment) + '\n')


def username_in_file(username):
    with open('done.txt') as f:
        if username in f.read():
            return 1
        else:
            return 0


def change_account():
    lista = []
    with open('ig_bot.txt', 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            lista.append(line)

    with open('ig_bot.txt', 'w') as fa:
        i = len(lista)
        while i > 0:
            if i == 1:
                fa.write(lista[i - 1])
            else:
                fa.write(lista[i - 1] + '\n')
            i -= 1


def get_bots_credentials():
    # Get bots credentials from file
    bot_credentials = []
    with open("ig_bot.txt", 'r', encoding='UTF-8') as botFile:
        while credentials := botFile.readline().rstrip():
            bot_credentials.append(credentials)
    return bot_credentials


def get_num_bots():
    return sum(1 for line in open('ig_bot.txt'))


def get_targets():
    # Get targets username from file
    targets = []
    with open("ig_target.txt", 'r', encoding='UTF-8') as targetFile:
        while target := targetFile.readline().rstrip():
            targets.append(target)
    return targets


def thread_function(credentials, target):
    # Create client
    cl = Client()
    credentials = credentials.split(':')
    try:
        filename = 'temp/dump_' + credentials[0] + '.json'
        print("First boot for these account? [Y/N]: ")
        x = input()
        if x == 'Y' or x == 'y':
            if not os.path.exists(filename):
                f = open(filename, "w")
                f.close()

            cl.login(credentials[0], credentials[1])
            cl.dump_settings(filename)
        else:
            cl.load_settings(filename)
            cl.login(credentials[0], credentials[1])
            cl.get_timeline_feed()

        print('Start using:', credentials[0])
    except:
        print("Something went wrong. Try to reset the account password of this account:", credentials[0])
    else:
        count_done = 0
        print("Working on:", target)

        try:
            id = get_user_id_from_username(cl, target)
        except:
            print("Account with info restrictions, skipping...")

        # Get target's following
        print("Getting following of:", target)
        try:
            following = cl.user_following(id)
            last_following_id = list(following.keys())[-1]
        except:
            print("Something went wrong. Check this account:", credentials[0])
            add_to_error(credentials[0], "Unable to get following")
        else:
            for user_id in following.keys():
                if count_done >= N_MSG_PER_BOT:
                    return
                if user_id == last_following_id:
                    print("Last Following Achieved")

                try:
                    username = cl.username_from_user_id(user_id)
                except:
                    print("Error getting user username.")
                    # username = user_id

                if username_in_file(username) == 0:
                    try:
                        print("Sending direct and comment to:", username)
                        send_direct(cl, user_id)
                        count_done += 1
                        print("Request sent with", credentials[0], ":", count_done)
                        try:
                            comment_last_post(cl, user_id)
                        except:
                            print("Unable to comment on the last post, private account.")
                            add_to_done(username, 0)
                        else:
                            add_to_done(username, 1)

                        time.sleep(DELAY)
                    except:
                        print("Private account with info restrictions.")


if __name__ == "__main__":
    # Formatting Log
    # format = "%(message)s"
    # logging.basicConfig(format=format, level=logging.INFO)
    # logging.info("Thread %s: starting %s", name, a)

    with concurrent.futures.ThreadPoolExecutor(max_workers=get_num_bots()) as executor:
        executor.map(thread_function, get_bots_credentials(), get_targets())
