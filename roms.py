#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shutil
import sys


def copy_whitelisted_files(console, dest_dir, base_dir):
    console_dest_dir = dest_dir + "/" + console
    whitelist_file = base_dir + "/" + console + "/whitelist.auto.txt"

    # Prompt to create console dir
    if not os.path.isdir(console_dest_dir):
        create_dir(console, console_dest_dir)

    # Get list of destination files
    dest_files = [f for f in os.listdir(
        console_dest_dir) if os.path.isfile(os.path.join(console_dest_dir, f))]

    with open(whitelist_file) as f:
        whitelist = f.read().splitlines()

    # Copy whitelisted destination files
    copy_list = [item for item in whitelist if item not in dest_files]
    if len(copy_list) >= 1:
        logging.info(console + ": updating whitelisted files to " +
                     console_dest_dir + "...")

        for f in copy_list:
            file_name = os.path.join(console_dest_dir, f.rstrip())
            if not os.path.isfile(file_name):
                shutil.copy2(base_dir + "/" + console +
                             "/" + f.rstrip(), file_name)
                logging.info(console + ": copied " +
                             f.rstrip() + " successfully.")

    logging.info(console + ": whitelisted destination files are up-to-date")


def create_dir(console, path):
    logging.warning(console + ": " + path + " does NOT exist, create it? y/N:")
    create = input()
    if create == "y" or create == "Y":
        os.mkdir(path)

        if not os.path.isdir(path):
            logging.critical(console + ": failed to create directory, exiting!: " +
                             path)
            exit(1)
        else:
            logging.info(console + ": created: " + path)
    else:
        logging.critical(console + ": unable to proceed, exiting!")
        exit(1)


def delete_blacklisted_files(console, dest_dir, base_dir):
    blacklist_file = base_dir + "/" + console + "/blacklist.auto.txt"
    console_dest_dir = dest_dir + "/" + console

    # Confirm final destinaton exists
    if not os.path.isdir(console_dest_dir):
        logging.critical(console + ": path does NOT exist, exiting!: " +
                         console_dest_dir)
        exit(1)

    # Get list of destination files
    dest_files = [f for f in os.listdir(
        console_dest_dir) if os.path.isfile(os.path.join(console_dest_dir, f))]

    with open(blacklist_file) as f:
        blacklist = f.read().splitlines()

    # Delete blacklisted destination files
    delete_files = [item for item in blacklist if item in dest_files]
    for f in delete_files:
        file_name = os.path.join(console_dest_dir, f.rstrip())
        try:
            os.remove(file_name)
            logging.info(console + ": successfully deleted " +
                         f.rstrip())
        except OSError as e:
            if e.errno != errno.ENOENT:  # Ignore "No such file or directory"
                raise

    logging.info(console + ": blacklisted destination files are up-to-date")


def generate_lists(console, base_dir):
    console_path = base_dir + "/" + console

    # Prompt to create console dir
    if not os.path.isdir(console_path):
        create_dir(console, console_path)

    # Initial list of files in console dir
    filelist = [f for f in os.listdir(
        console_path) if os.path.isfile(os.path.join(console_path, f))]

    # Remove ignored files by extension
    ignored_extensions_regex = "(?!.*\.txt$)(?!.*\.auto$)(?!.*\.png$)(?!.*\.srm$)(?!.*\.xml$)"
    filelist = list(
        filter(lambda v: re.match(ignored_extensions_regex, v), filelist))

    # Replace "Enhance" with "TEMPORARY" to guarantee "(En)" search result accuracy
    filelist = [file.replace('Enhance', 'TEMPORARY') for file in filelist]

    # Blacklist [b], (Beta), [BIOS], (Demo), (Program), (Proto), and (Sample)
    regex_bios = ".*\[b\].*|.*\(.*Beta.*\).*|.*[Bb][Ii][Oo][Ss].*|.*\(.*Demo.*\).*|.*\(.*Program.*\).*|.*\(.*Proto.*\).*|.*\(.*Sample.*\).*"
    blacklist = list(
        filter(lambda v: re.match(regex_bios, v), filelist))

    # Blacklist files that are not (U), (USA), (World), (En)
    regex_not_english = "(?!.*\(U\).*)(?!.*\(.*USA.*\).*)(?!.*\(.*World.*\).*)(?!.*\(.*En.*\).*)"
    blacklist = blacklist + list(
        filter(lambda v: re.match(regex_not_english, v), filelist))

    # Replace "TEMPORARY" with "Enhance"
    blacklist = [file.replace('TEMPORARY', 'Enhance') for file in blacklist]

    # Add blacklist custom (if it exists) to blacklist auto
    blacklist_custom_path = console_path + "/blacklist.custom.txt"
    if os.path.exists(blacklist_custom_path):
        with open(blacklist_custom_path) as blacklist_custom:
            blacklist = blacklist + blacklist_custom.read().splitlines()

    # Alphabetize and remove duplicates
    blacklist = sorted(
        list(dict.fromkeys(blacklist)))

    # Whitelist files that are not (Beta), [BIOS], (Demo), and (Program)
    regex_not_bios = "(?!.*\(.*Beta.*\).*)|(?!.*[Bb][Ii][Oo][Ss].*)|(?!.*\(.*Demo.*\).*)|(?!.*\(.*Program.*\).*)|(?!.*\(.*Proto.*\).*)"
    whitelist = list(
        filter(lambda v: re.match(regex_not_bios, v), filelist))

    # Whitelist files that are (U), (USA), (World), (En)
    regex_english = ".*\(U\).*|.*\(.*USA.*\).*|.*\(.*World.*\).*|.*\(.*En.*\).*"
    whitelist = list(
        filter(lambda v: re.match(regex_english, v), whitelist))

    # Replace "TEMPORARY" with "Enhance"
    whitelist = [file.replace('TEMPORARY', 'Enhance') for file in whitelist]

    # Subtract blacklist auto from whitelist auto
    whitelist = [item for item in whitelist if item not in blacklist]

    # Add whitelist custom (if it exists) to whitelist auto
    whitelist_custom_path = console_path + "/whitelist.custom.txt"
    if os.path.exists(whitelist_custom_path):
        with open(whitelist_custom_path) as whitelist_custom:
            whitelist = whitelist + whitelist_custom.read().splitlines()

    # Alphabetize and remove duplicates
    whitelist = sorted(
        list(dict.fromkeys(whitelist)))

    # Subtract whitelist auto from blacklist auto, finalize blacklist auto
    blacklist = [item for item in blacklist if item not in whitelist]

    # Write whitelist to file
    whitelist_path = console_path + "/whitelist.auto.txt"
    with open(whitelist_path, "w") as white_file:
        for file_line in whitelist:
            white_file.write('%s\n' % file_line)
    logging.info(console + ": blacklist generated")

    # Write blacklist to file
    blacklist_path = console_path + "/blacklist.auto.txt"
    with open(blacklist_path, "w") as black_file:
        for file_line in blacklist:
            black_file.write('%s\n' % file_line)
    logging.info(console + ": whitelist generated")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler()],
    )

    description = "Automatically filter video game roms using blacklists and whitelists and (optionally) transfer them."

    parser = argparse.ArgumentParser(
        description=description)
    parser.add_argument("--base-dir")
    parser.add_argument("--console-name", required=True)
    parser.add_argument("--destination-dir")
    args = parser.parse_args()

    if not args.base_dir:
        logging.warning(
            "missing --base-dir argument, falling back to current working directory (" + os.getcwd() + ")!")
        base_dir = os.getcwd()
    else:
        base_dir = args.base_dir

    if args.console_name == "all":
        console_dirs = ["gb", "gba", "gbc", "genesis",
                        "n64", "nes", "psp", "psx", "snes"]
    else:
        console_dirs = [args.console_name]

    if not args.destination_dir:
        logging.warning(
            "missing --destination-dir argument, NOT syncing files to destination directory!")

    for console in console_dirs:
        generate_lists(console, base_dir)

        if args.destination_dir:
            copy_whitelisted_files(console, args.destination_dir, base_dir)
            delete_blacklisted_files(console, args.destination_dir, base_dir)
