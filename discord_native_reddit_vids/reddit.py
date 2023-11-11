import re

# Matches reddit urls
# https://www.reddit.com/r/ihaveihaveihavereddit/comments/9jg8k7/this_is_so_true/
# https://v.redd.it/1e0vq1k2j9p71
url_regex = re.compile(
    r"(https?\:\/\/((old\.|www\.)?reddit\.com\/r\/[\w]+\/comments\/[\w]+\/\S*|v\.redd\.it\/\S+))",
    re.IGNORECASE,
)


def get_reddit_urls(message_content: str):
    """Returns a list of reddit urls in a message"""
    matches = url_regex.findall(message_content)
    # join tuple of groups into a string
    return [match[0] for match in matches]
