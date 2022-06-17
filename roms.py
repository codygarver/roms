#!/usr/bin/env python3

import argparse
import copy
import hashlib
import logging
import os
import pathlib
import re
import shutil


def copy_whitelisted_files(console, dest_dir, base_dir):
    console_dest_dir = pathlib.Path(dest_dir, console)

    # Prompt to create console dir
    if not console_dest_dir.is_dir():
        create_dir(console, console_dest_dir)

    whitelist_file = pathlib.Path(base_dir, console, "whitelist.auto.txt")
    whitelist = whitelist_file.read_text().splitlines()

    # Copy whitelisted games' images to destination if they exist
    images_dir = pathlib.Path(base_dir, console, "images")
    if not args.no_images and images_dir.is_dir():
        imagelist = []
        for f in whitelist:
            src_file = pathlib.Path(base_dir, console, f)
            basename = src_file.stem
            imagelist = imagelist + images_dir.glob(basename + "*.png")

        if imagelist:
            whitelist = sorted(
                list(dict.fromkeys(whitelist + imagelist)))
            images_dest_dir = pathlib.Path(console_dest_dir, "images")
            images_dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy whitelisted games' manuals to destination if they exist
    manuals_dir = pathlib.Path(base_dir, console, "manuals")
    if not args.no_manuals and manuals_dir.is_dir():
        manuallist = []
        for f in whitelist:
            src_file = pathlib.Path(base_dir, console, f)
            basename = src_file.stem
            manuallist = manuallist + manuals_dir.glob(basename + "*.pdf")

        if manuallist:
            whitelist = sorted(
                list(dict.fromkeys(whitelist + manuallist)))
            manuals_dest_dir = pathlib.Path(console_dest_dir, "manuals")
            manuals_dest_dir.mkdir(parents=True, exist_ok=True)

    elif not manuals_dir.is_dir():
        logging.warning(
            console + ": not copying manuals because dir does not exist: " +
            str(manuals_dir))

    # Copy whitelisted destination files
    if whitelist:
        logging.info(console + ": updating whitelisted files in " +
                     str(console_dest_dir) + ", large files may take a while...")

        def get_hash(file):
            file_hash = hashlib.blake2b(pathlib.Path(
                file).read_bytes()).hexdigest()

            return file_hash

        for f in whitelist:
            dest_file = pathlib.Path(console_dest_dir, f)
            src_file = pathlib.Path(base_dir, console, f)

            dest_hash = ""
            src_hash = get_hash(src_file)
            if dest_file.is_file():
                dest_hash = get_hash(dest_file)

            if not dest_file.is_file() or dest_hash != src_hash:
                shutil.copy2(src_file, dest_file)

                dest_hash = get_hash(dest_file)

                if dest_hash == src_hash:
                    logging.info(console + ": copied " + dest_file.name)
                else:
                    logging.critical(console + ": hash sum mismatch (I/O error?), exiting!: " +
                                     dest_file.name)
            elif dest_hash == src_hash:
                logging.info(console + ": verified " + dest_file.name)

    logging.info(console + ": whitelisted destination files are up-to-date")


def create_dir(console, path):
    path = str(path)

    def mkdir(path):
        os.mkdir(path)

        if not os.path.isdir(path):
            logging.critical(console + ": failed to create directory, exiting!: " +
                             path)
            exit(1)
        else:
            logging.info(console + ": created: " + path)

    if not args.initialize:
        logging.warning(console + ": " + path +
                        " does NOT exist, create it? y/N:")
        create = input()
        if create == "y" or create == "Y":
            mkdir(path)
        else:
            logging.critical(console + ": unable to proceed, exiting!")
            exit(1)
    else:
        mkdir(path)


def delete_blacklisted_files(console, dest_dir, base_dir):
    blacklist_file = pathlib.Path(base_dir, console, "blacklist.auto.txt")
    blacklist = blacklist_file.read_text().splitlines()
    console_dest_dir = pathlib.Path(dest_dir, console)

    # Confirm final destinaton exists
    if not console_dest_dir.is_dir():
        logging.critical(console + ": path does NOT exist, exiting!: " +
                         str(console_dest_dir))
        exit(1)

    # Get list of destination files
    dest_files = [f.name for f in console_dest_dir.glob(
        "*") if f.is_file()]

    # Delete blacklisted destination files
    delete_files = [item for item in blacklist if item in dest_files]
    for f in delete_files:
        pathlib.Path(console_dest_dir, f).unlink(missing_ok=True)
        logging.info(
            console + ": deleted " + f)

    logging.info(console + ": blacklisted destination files are up-to-date")


def generate_lists(console, base_dir):
    console_path = pathlib.Path(base_dir, console)

    # Prompt to create console dir
    if not console_path.is_dir():
        create_dir(console, console_path)

    # Initial list of files in console dir
    filelist = [f.name for f in console_path.glob(
        "*") if f.is_file()]

    # Remove ignored files by extension
    ignored_extensions_regex = "(?!\..*$)(?!.*\.auto$)(?!.*\.png$)(?!.*\.sql$)(?!.*\.srm$)(?!.*\.torrent$)(?!.*\.txt$)(?!.*\.xml$)"
    filelist = list(
        filter(lambda v: re.match(ignored_extensions_regex, v), filelist))

    # Blacklist [b], (Beta), [BIOS], (Demo), (Pirate), (Program), (Proto), and (Sample)
    regex_bios = ".*[Aa]ction.*[Rr]eplay.*|.*Bible.*|.*Cheat.*Code.*|.*Demo.*(CD|Disc).*|.*Game.*Boy.*Camera.*|.*Game[Ss]hark.*|.*InfoGenius.*|.*Personal.*Organizer.*|.*Preview.*|.*Sewing.*Machine.*Operation.*Software.*|.*System.*Kiosk.*|.*[Bb][Ii][Oo][Ss].*|.*\(.*Beta.*\).*|.*\(.*Debug.*\).*|.*\(.*Demo.*\).*|.*\(.*Pirate.*\).*|.*\(.*Program.*\).*|.*\(.*Proto.*\).*|.*\(.*Sample.*\).*|.*\[b\].*"
    bios_list = list(
        filter(lambda v: re.match(regex_bios, v), filelist))

    combos_list = []
    if args.no_combos:
        regex_combos = "^([Cc]ombo|\d|.*([Tt](wo|hree)|[Dd]ouble|[Ff](our|ive)|[Ss](ix|even)|[Ee](ight|even)|[Ee](ight|even)|[Nn]ine|[Tt]en)).*([Gg]ame|([Ii]n.*(1|[Oo]ne)|[Pp]a(ck|k)))"
        combos_list = list(
            filter(lambda v: re.match(regex_combos, v), filelist))

    boardgame_list = []
    if args.no_boardgames:
        regex_boardgames = ".*Board[Gg]ame.*|.*Board\sGame.*|.*Brain.*Game.*|.*Caesars\sPalace.*|.*Card\sGames.*|.*Chess.*|.*Family.*Feud.*|.*Fun.*Pak.*|.*Gambling.*|.*Puzzle.*|.*Quiz.*|.*Scrabble.*|.*Sudoku.*|.*[Uu][Nn][Oo].*|.*Vegas.*Games.*|.*Vegas.*Stakes.*|.*Wheel.*Fortune.*|.*Who.*Wants.*Millionaire.*|.*[Uu][Nn][Oo].*"
        boardgame_list = list(
            filter(lambda v: re.match(regex_boardgames, v), filelist))

    kids_list = []
    if args.no_kids:
        regex_kids = ".*Arthur\!.*|.*Barbie.*|.*Beauty.*Beast.*|.*Berenstain.*Bears.*|.*Blue.*Clues.*|.*Bob.*Builder.*|.*Bratz.*|.*Britney.*Dance.*Beat.*|.*Cat\sin\sthe\sHat.*|.*Cheetah.*Girls.*|.*Despicable\sMe.*|.*Disney.*|.*Dogz.*|.*Dora.*Explor.*|.*Dr.*Seuss.*|.*Drake.*Josh.*|.*Dragon\sTales.*|.*everGirl.*|.*Every\sChild\sCan\sSucceed.*|.*Fun.*Learn.*|.*Kim.*Possible.*|.*Land.*Before.*Time.*|.*Lilo.*Stitch.*|.*Little.*Einsteins.*|.*Little.*Mermaid.*|.*Lizzie.*McGuire.*|.*Mary.*Kate.*Ashley.*|.*Nancy.*Drew.*|.*NeoPets.*|.*Nickelodeon.*|.*Petz.*|.*Princess.*Natasha.*|.*Pooh.*|.*Sabrina.*Teenage.*Witch.*|.*Sesame\sStreet.*|.*Shrek.*|.*Snow.*White.*|.*Strawberry.*Shortcake.*|.*Stuart.*Little.*|.*That.*So.*Raven.*|.*Tonka.*|.*Totally.*Spies.*|.*Trollz.*|.*VeggieTales.*|.*Zoey.*101.*|.*Zoboomafoo.*|.*[Ww][Ii][Nn][Xx].*"
        kids_list = list(
            filter(lambda v: re.match(regex_kids, v), filelist))

    racing_list = []
    if args.no_racing:
        regex_racing = ".*(1|2|3)Xtreme.*|.*ATV.*|.*BMX.*|.*Biking.*|.*Driv3r.*|.*F1.*|.*Ferrari.*|.*Ford.*|.*Formula\s(1|One).*|.*Grand.*Prix.*|.*Harley.*Davidson.*|.*Hot.*Wheels.*|.*Lamborghini.*American.*Challenge.*|.*Madden.*|.*Micro.*Machines.*|.*Motocross.*|.*NASCAR.*|.*Road.*Rash.*|.*Roadsters.*|.*Scooter.*|.*Super(bike|cross).*|.*Test.*Drive.*|.*Top.*Gear.*|.*Touring.*Car.*|.*V\-Rally.*|.*Xtreme.*Wheels.*|.*[Rr]ace.*|.*Racing.*|.*Mototrax.*|.*Monster.*Jam.*|.*XS.*Moto.*|.*xXx.*"
        racing_list = list(
            filter(lambda v: re.match(regex_racing, v), filelist))

    sports_list = []
    if args.no_sports:
        regex_sports = ".*[Bb]aseball.*|.*Bases.*Loaded.*|.*Bass.*(Challenge|Championship).*|.*Big\sOl.*Bass.*|.*Billiards.*|.*Boarder.*|.*Bottom\sof\sthe\s9th.*|.*Bowling.*|.*Boxing.*|.*Cabela.*|.*Darts.*|.*ECW.*|.*ESPN.*|.*FIFA*|.*Faire\sGames.*|.*Fisherman.*|.*Fishing.*|.*Football.*|.*Golf.*|.*Hockey.*|.*Karnaaj.*Rally.*|.*MLB.*|.*MotoGP.*|.*MX.*2000.*|.*NBA.*|.*NCAA.*|.*NFL.*|.*NHL.*|.*Olympic.*|.*PGA.*|.*Poker.*|.*Pool.*|.*Skate.*|.*Soccer.*|.*Sports.*|.*Super.*Bowl.*|.*TNA\sImpact.*|.*Tennis.*|.*Toobin.*|.*UEFA.*|.*UFC.*|.*Ultimate.*Fighting.*Championship.*|.*Ultimate.*Paintball.*|.*Ultimate.*Surfing.*|.*Wakeboard.*|.*WCW.*|.*WRC.*|.*WWE.*|.*WWF.*|.*World.*Cup.*|.*Wrestling.*"
        sports_list = list(
            filter(lambda v: re.match(regex_sports, v), filelist))

    virtual_console_list = []
    if args.no_virtual_console:
        regex_virtual_console = ".*[Vv]irtual.*[Cc]onsole.*"
        virtual_console_list = list(
            filter(lambda v: re.match(regex_virtual_console, v), filelist))

    gba_videos_list = []
    if args.no_gba_videos:
        regex_gba_videos = ".*Game.*Boy.*Advance.*Video.*"
        gba_videos_list = list(
            filter(lambda v: re.match(regex_gba_videos, v), filelist))

    # Replace "Enhance" with "TEMPORARY" to guarantee "(En)" search result accuracy
    filelist = [file.replace('Enhance', 'TEMPORARY') for file in filelist]

    # Blacklist files that are not (U), (USA), (World)
    regex_not_english = "(?!.*\(U\).*)(?!.*\(.*US.*\).*)(?!.*\(.*USA.*\).*)(?!.*\(.*World.*\).*)"
    not_english = list(
        filter(lambda v: re.match(regex_not_english, v), filelist))

    # Replace "TEMPORARY" with "Enhance"
    not_english = [file.replace('TEMPORARY', 'Enhance')
                   for file in not_english]

    # Replace "TEMPORARY" with "Enhance"
    filelist = [file.replace('TEMPORARY', 'Enhance') for file in filelist]

    # Add extra lists to blacklist
    blacklist = sorted(
        list(dict.fromkeys(bios_list + combos_list + boardgame_list + gba_videos_list + kids_list + not_english + racing_list + sports_list + virtual_console_list)))

    whitelist = [item for item in filelist if item not in blacklist]

    # List filenames including Rev
    regex_revision = ".*\(Rev.*\d\).*"

    rev_files = list(
        filter(lambda v: re.match(regex_revision, v), whitelist))

    # Build dictionaries containing filenames and Revs
    rev_dict_all = {}

    for f in rev_files:
        filename_without_rev = re.sub(
            "\(Rev.*\d\)", "REPLACE_WITH_REV", f)

        rev = re.findall("\(Rev.*\d\)", f)[0]

        if filename_without_rev not in rev_dict_all:
            rev_dict_all.update({filename_without_rev: {
                "revisions": [rev]
            }})
        else:
            rev_dict_all[filename_without_rev]["revisions"].append(
                rev)

    # Copy the dict because it's unsafe to modify the original data structure while iterating over it
    rev_dict_min = copy.deepcopy(rev_dict_all)

    # Whitelist greatest Revs
    for filename in rev_dict_all:
        # Get the greatest Rev and whitelist it
        max_ver = max(rev_dict_all[filename]["revisions"])

        game_file = re.sub(
            "REPLACE_WITH_REV", max_ver, filename)

        whitelist = whitelist + [game_file]

        # Remove the greatest Rev from the minor Rev dictionary
        rev_dict_min[filename]["revisions"].remove(max_ver)

        # Get the filename without any Rev
        game_file = re.sub(
            " REPLACE_WITH_REV", "", filename)

        # Confirm the reconstructed filename exists
        if game_file in filelist:
            if game_file in whitelist:
                # Keep the whitelist in sync
                whitelist.remove(game_file)

            # Blacklist the filename without any Rev
            blacklist = blacklist + [game_file]

    # Blacklist all inferior Revs
    for filename in rev_dict_min:
        for rev in rev_dict_min[filename]["revisions"]:
            game_file = re.sub(
                "REPLACE_WITH_REV", rev, filename)

        # Confirm the reconstructed filename exists
        if game_file in filelist:
            if game_file in whitelist:
                # Keep the whitelist in sync
                whitelist.remove(game_file)

            blacklist = blacklist + [game_file]

    # Add blacklist custom (if it exists) to blacklist auto
    blacklist_custom_path = pathlib.Path(console_path, "blacklist.custom.txt")
    if blacklist_custom_path.is_file():
        blacklist = blacklist + blacklist_custom_path.read_text().splitlines()

    # Alphabetize and remove duplicates
    blacklist = sorted(
        list(dict.fromkeys(blacklist)))

    # Subtract blacklist auto from whitelist auto
    whitelist = [item for item in whitelist if item not in blacklist]

    # Add whitelist custom (if it exists) to whitelist auto
    whitelist_custom_path = pathlib.Path(console_path, "whitelist.custom.txt")
    if whitelist_custom_path.is_file():
        whitelist = whitelist + whitelist_custom_path.read_text().splitlines()

    # Alphabetize and remove duplicates
    whitelist = sorted(
        list(dict.fromkeys(whitelist)))

    # Subtract whitelist auto from blacklist auto, finalize blacklist auto
    blacklist = [item for item in blacklist if item not in whitelist]

    # Write whitelist to file
    whitelist_path = pathlib.Path(console_path, "whitelist.auto.txt")
    whitelist_path.unlink(missing_ok=True)
    with whitelist_path.open('a') as whitelist_file:
        for file_line in whitelist:
            whitelist_file.write(file_line + "\n")
    logging.info(console + ": whitelist generated")

    # Write blacklist to file
    blacklist_path = pathlib.Path(console_path, "blacklist.auto.txt")
    blacklist_path.unlink(missing_ok=True)
    with blacklist_path.open('a') as blacklist_file:
        for file_line in blacklist:
            blacklist_file.write(file_line + "\n")
    logging.info(console + ": blacklist generated")


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
    parser.add_argument("--initialize", action='store_true')
    parser.add_argument("--no-boardgames", action='store_true')
    parser.add_argument("--no-combos", action='store_true')
    parser.add_argument("--no-gba-videos", action='store_true')
    parser.add_argument("--no-images", action='store_true')
    parser.add_argument("--no-kids", action='store_true')
    parser.add_argument("--no-manuals", action='store_true')
    parser.add_argument("--no-racing", action='store_true')
    parser.add_argument("--no-sports", action='store_true')
    parser.add_argument("--no-virtual-console", action='store_true')
    args = parser.parse_args()

    if not args.base_dir:
        base_dir = str(pathlib.Path.cwd())
        logging.warning(
            "missing --base-dir argument, falling back to current working directory (" + base_dir + ")!")
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
