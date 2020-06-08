from bs4 import BeautifulSoup
from tqdm import tqdm
import click
import cloudscraper
import glob
import img2pdf
import logging
import math
import os
import platform
import queue
import re
import requests
import shutil
import threading
import traceback


def easy_slug(string, repl='-', directory=False):
    if directory:
        return re.sub(r"^\.|\.+$", "", easy_slug(string, directory=False))
    else:
        return re.sub(r"[\\\\/:*?\"<>\|]|\ $", repl, string)


def page_downloader(url: str, scraper_delay: int = 10, **kwargs):
    headers = kwargs.get('headers')
    if not headers:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Accept-Encoding': 'gzip, deflate',
        }

    session = requests.session()
    session = cloudscraper.create_scraper(session, delay=scraper_delay)

    connection = session.get(url, headers=headers,
            cookies=kwargs.get('cookies'))

    if connection.status_code != 200:
        click.secho('Whoops! Seems like I can not connect to the website.',
                fg='red')
        click.echo(f'It is showing: {connection}')
        raise Warning(f'Can not connect to website {url}')
    else:
        page_source = BeautifulSoup(connection.text.encode('utf-8'),
            'html.parser')
        connection_cookies = session.cookies

        return page_source, connection_cookies


def downloader(image_and_name, referer, directory, **kwargs):

    pbar = kwargs.get('pbar')

    image_ddl = image_and_name[0]
    filename = image_and_name[1]
    filepath = os.path.join(directory, filename)

    if os.path.isfile(filepath):
        pbar.write(f'[comics.py] File exists! Skipping: {filename}\n')
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': referer,
        }

        session = requests.session()
        session = cloudscraper.create_scraper(session)

        try:
            r = session.get(image_ddl, stream=True, headers=headers,
                    cookies=kwargs.get('cookies'))
            r.raise_for_status()
            if r.status_code != 200:
                pbar.write('Could not download the image.')
                pbar.write(f'Link status: {r.status_code}')
            else:
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                filepath = os.path.normpath(filename)

                try:
                    shutil.move(filepath, directory)
                except Exception as e:
                    pbar.write(e)
                    os.remove(filepath)
                    raise e
        except requests.exceptions.HTTPError as eh:
            pbar.write('HTTP error:')
            pbar.write(eh)
            raise
        except requests.exceptions.ConnectionError as ec:
            pbar.write('Error connecting:')
            pbar.write(ec)
            raise
        except requests.exceptions.Timeout as et:
            pbar.write('Timeout error:')
            pbar.write(et)
            raise
        except requests.exceptions.RequestException as er:
            pbar.write('Oops (something else):')
            pbar.write(er)
            raise
        except Exception as e:
            pbar.write('A problem ocurred while downloading this image: '
                    f'{filename}')
            pbar.write(eh)
            raise

    pbar.update()


def convert_files(chapter_number, comic_name, directory, keep, pdf):

    main_dir = str(directory).split(os.sep)
    main_dir.pop()
    converted_file_dir = str(os.sep.join(main_dir)) + os.sep

    # TODO: conversion to other formats than pdf
    if pdf:
        images = [
            imgs
            for imgs
            in sorted(glob.glob(str(directory) + '/*.jpg'),
                key=lambda x: int(str(x.split('.')[0]).split(os.sep)[-1]))
        ]
        pdf_file = str(converted_file_dir) + "{0} - Ch {1}.pdf".format(
                easy_slug(comic_name), chapter_number)

        try:
            if os.path.isfile(pdf_file):
                click.secho(f'PDF file exists! Skipping: {pdf_file}',
                    fg='yellow')
            else:
                with open(pdf_file, 'wb') as f:
                    f.write(img2pdf.convert(images))

                click.secho('Converted the images to pdf.', fg='green')
        except Exception as e:
            click.secho('Could not write the pdf file...', fg='red')
            click.echo(e)

            # don't delete if the conversion failed
            keep = True

    if not keep:
        try:
            shutil.rmtree(path=directory, ignore_errors=True)
        except Exception as e:
            click.secho('Could not delete images.', fg='yellow')
            click.echo(e)

        click.echo('Deleted the image files.')


def multithreaded_download(chapter_number, comic_name, url, directory,
        filenames, links, pool_size=4):

    def worker():
        while True:
            try:
                worker_item = in_queue.get()
                downloader(worker_item, url, directory, pbar=pbar)
                in_queue.task_done()
            except queue.Empty:
                return
            except Exception as e:
                err_queue.put(e)
                in_queue.task_done()

    in_queue = queue.Queue()
    err_queue = queue.Queue()

    pbar = tqdm(links, leave=True, unit='img/s', position=0)
    pbar.set_description(f'[comics.py] Downloading: {comic_name} '
            f'[{chapter_number}] ')

    for _ in range(pool_size):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    for item in zip(links, filenames):
        in_queue.put(item)

    in_queue.join()

    try:
        err = err_queue.get(block=False)
        pbar.set_description(f'[comics.py] Error: {comic_name} '
                f'[{chapter_number}] - {err}')
        raise err
    except queue.Empty:
        pbar.set_description(f'[comics.py] Done: {comic_name} '
                f'[{chapter_number}] ')
        return 0
    finally:
        pbar.close()


def prepend_zeros(current_chapter, total_images):
    max_digits = int(math.log10(int(total_images))) + 1
    return str(current_chapter).zfill(max_digits)


def single_chapter(url: str, comic_name: str, directory: str, keep: bool,
        pdf: bool):

    chapter_number = str(url).split('/')[5].split('?')[0].replace('-', ' - ')
    soup, _ = page_downloader(url)

    img_list = re.findall(r'lstImages.push\(\"(.*?)\"\);', str(soup))

    download_directory = os.path.join(directory, comic_name, chapter_number)
    if not os.path.isdir(download_directory):
        os.makedirs(download_directory)

    links = []
    filenames = []
    for current_chapter, image_link in enumerate(img_list):
        image_link = image_link.replace('\\', '')

        # highest quality
        image_link = image_link. \
                replace('=s1600', '=s0'). \
                replace('/s1600', '/s0')

        current_chapter += 1
        file_name = prepend_zeros(current_chapter, len(img_list)) + '.jpg'
        filenames.append(file_name)
        links.append(image_link)

    multithreaded_download(chapter_number, comic_name, url, download_directory,
            filenames, links)
    convert_files(chapter_number, comic_name, download_directory, keep, pdf)
