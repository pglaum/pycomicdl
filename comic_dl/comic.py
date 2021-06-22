#!/usr/bin/env python3

from bs4 import BeautifulSoup  # type: ignore
from urllib.parse import urljoin, urlsplit, urlunsplit
from .helpers import page_downloader, single_chapter
import click
import html
import os
import re
import traceback

basedir = os.path.abspath(os.path.dirname(__file__))


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx: click.core.Context, debug: bool) -> None:
    """Initialize the CLI context.
    """

    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug


@cli.command('search')
@click.argument('keyword')
@click.option('--results', '-r', type=int, default=5,
              help='Maximum results [Default: 5]')
@click.option('--base-url', '-u', 'base_url', type=str,
              default='https://readcomiconline.li',
              help='Base url of readcomiconline '
                   '[Default: https://readcomiconline.li]')
@click.pass_context
def search(ctx: click.core.Context, keyword: str, results: int, base_url: str) -> None:
    """Search for a comicbook series.
    """

    if not base_url.startswith('http'):
        click.secho('Error: no scheme provided. Did you mean '
                    f'https://{base_url}?', fg='red')
        exit(1)

    click.secho('All HTML downloads will take some time, because we have to '
                'fool CloudFlare.', fg='yellow')
    click.secho(f'Searching for "{keyword}"...', fg='green')

    data = {
        'keyword': keyword,
    }

    soup, _ = page_downloader(urljoin(base_url, 'Search/Comic'),
                              data=data, method='POST')

    all_links = []

    listings = soup.find_all('table', {'class': 'listing'})
    for elements in listings:
        tds = elements.find_all('td')
        for td in tds:
            try:
                result = html.unescape(td['title'])
                result = BeautifulSoup(result, 'html.parser')
                href = result.find('a')['href'].strip()
                href = urljoin(base_url, href)
                title = result.find('a').text.strip()
                description = result.find('p').text.strip()
                all_links.append({
                    'title': title,
                    'href': href,
                    'description': description,
                })
            except BaseException:
                pass

    for link in all_links[:results]:
        click.echo('- ' + link['title'])
        click.echo('  ' + link['href'])
        click.echo('  ' + link['description'])


@cli.command('download')
@click.argument('url')
@click.option('--directory', '-d', default='downloads', help='The directory '
              'to download to')
@click.option('--keep/--no-keep', default=True, help='Keep raw image files '
              'after converting to pdf [Default: True]')
@click.option('--pdf/--no-pdf', default=True, help='Convert images to pdf '
              '[Default: True]')
@click.pass_context
def download(ctx: click.core.Context, url: str, directory: str, keep: bool, pdf: bool) -> None:
    """Download a comicbook series or chapter.

    The URL can be a link to a chapter or series on readcomiconline.
    If URL leads to a series, all chapters will be downloaded.
    """

    comic_name = url.split('/')[4].strip()
    comic_name = re.sub(r'[0-9][a-z][A-Z]\ ', '', str(comic_name))
    comic_name = str(comic_name.title()).replace('-', ' ')

    url_split = str(url).split('/')

    split = urlsplit(url)
    base_url = urlunsplit((split.scheme, split.netloc, '', '', ''))

    if len(url_split) in [5]:
        # this is a comicbook series

        click.secho(
            'All HTML downloads will take some time, because we have to '
            'fool CloudFlare.', fg='yellow')
        click.secho(f'Downloading "{comic_name}"...', fg='green')

        click.secho('Getting series url...', fg='green')
        soup, _ = page_downloader(url)

        all_links = []

        listings = soup.find_all('table', {'class': 'listing'})
        for elements in listings:
            links = elements.find_all('a')
            for link in links:
                all_links.append(str(link['href']).strip())

        all_links.reverse()

        for chapter_link in all_links:
            chapter_link = urljoin(base_url, chapter_link)

            try:
                single_chapter(chapter_link, comic_name, directory, keep, pdf)
            except Exception:
                click.secho('An exception ocurred while trying to download '
                            f'{chapter_link}.', fg='red')
                traceback.print_exc()

    else:

        click.secho(f'Downloading "{comic_name}"...', fg='green')
        click.secho('All HTML downloads will take some time, because we have '
                    'to fool CloudFlare.', fg='yellow')

        if '&readType=0' in url:
            # All images on one page
            url = str(url).replace('&readType=0', '&readType=1')

        single_chapter(url, comic_name, directory, keep, pdf)


if __name__ == '__main__':
    cli()
