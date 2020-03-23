import re
import requests
import json
import logging
import base64
import os

def strip_description_data(body_data=None):
    """Resolve jira format test/data to markdown format"""
    def panel_table_resolve_data(data):
        lines = data.count('\n')
        resolved_group = re.sub(r'\s?\n?\s\n', r'\r\n', data, flags=re.DOTALL) # removing newline and double newlines
        for i in range(lines+3):
            if i is 1:
                resolved_group = re.sub(r'\s*?\n?[^0-9a-zA-Z]?{}\. '.format(i), r'{} - '.format(i), resolved_group.encode('ascii', 'ignore'))
            else:
                resolved_group = re.sub(r'\s*\n?[^0-9a-zA-Z]?{}\. '.format(i), r'\n{} - '.format(i), resolved_group.encode('ascii', 'ignore'))
        resolved_group = re.sub(r'^ \r?\n?', r'', resolved_group)
        return resolved_group

    def resolve_panel_group(match):
        return '\n| {} |\n| --- |\n| {} |\n'.format(match.group(1).encode('ascii', 'ignore'), panel_table_resolve_data(match.group(4).encode('ascii', 'ignore')))
    body = body_data
    body = re.sub(r'(\r\n){1}', r'  \1', body) # line breaks
    body = re.sub(r'\{code:([a-z]+)\}\s*', r'\n```\1\n', body) # Block code
    body = re.sub(r'\{code\}\s*', r'\n```\n', body) # Block code
    body = re.sub(r'\{noformat\}\s*', r'\n```\n', body) # Block code
    body = re.sub(r'\n\s*bq\. (.*)\n', r'\n\> \1\n', body) # Block quote
    body = re.sub(r'\{quote\}', r'\n\>\>\>\n', body) # Block quote #2
    body = re.sub(r'\{color:[\#\w]+\}(.*)\{color\}', r'> **\1**', body) # Colors
    body = re.sub(r'\n-{4,}\n', r'---', body) # Ruler
    body = re.sub(r'\[~([a-z]+)\]', r'@\1', body) # Links to users
    body = re.sub(r'\[([^|\]]*)\]', r'\1', body) # Links without alt
    #body = re.sub(r'\[(?:(.+)\|)([a-z]+://.+)\]', r'[\1](\2)', body) # Links with alt
    body = re.sub(r'\s?\n?\[([^|]*)\|([^]]*)\]', r'[\1]:\2', body)
    body = re.sub(r'\n *\# ', r'\n 1. ', body) # Ordered list
    body = re.sub(r'\n *[\*\-\#]\# ', r'\n   1. ', body) # Ordered sub-list
    body = re.sub(r'\n *[\*\-\#]{2}\# ', r'\n     1. ', body) # Ordered sub-sub-list
    body = re.sub(r'\n *\* ', r'\n - ', body) # Unordered list
    body = re.sub(r'\n *[\*\-\#][\*\-] ', r'\n   - ', body) # Unordered sub-list
    body = re.sub(r'\n *[\*\-\#]{2}[\*\-] ', r'\n     - ', body) # Unordered sub-sub-list
    # Text effects
    body = re.sub(r'(^|[\W])\*(\S.*\S)\*([\W]|$)', r'\1**\2**\3', body) # Bold
    body = re.sub(r'(^|[\W])_(\S.*\S)_([\W]|$)', r'\1*\2*\3', body) # Emphasis
    body = re.sub(r'(^|[\W])-(\S.*\S)-([\W]|$)', r'\1~~\2~~\3', body) # Deleted / Strikethrough
    body = re.sub(r'(^|[\W])~~-(\S.*\S)-~~([\W]|$)', r'\1-\2-\3', body) # Replace / Unwanted Strikethrough
    body = re.sub(r'(^|[\W])\+(\S.*\S)\+([\W]|$)', r'\1__\2__\3', body) # Underline
    body = re.sub(r'(^|[\W])\{\{(.*)\}\}([\W]|$)', r'\1`\2`\3', body) # Inline code
    # Titles
    body = re.sub(r'\n?\bh1\. ', r'\n# ', body)
    body = re.sub(r'\n?\bh2\. ', r'\n## ', body)
    body = re.sub(r'\n?\bh3\. ', r'\n### ', body)
    body = re.sub(r'\n?\bh4\. ', r'\n#### ', body)
    body = re.sub(r'\n?\bh5\. ', r'\n##### ', body)
    body = re.sub(r'\n?\bh6\. ', r'\n###### ', body)
    body = re.sub(r':\)', r':smiley:', body)
    body = re.sub(r':\(', r':disappointed:', body)
    body = re.sub(r':P', r':yum:', body)
    body = re.sub(r':D', r':grin:', body)
    body = re.sub(r';\)', r':wink:', body)
    body = re.sub(r'\(y\)', r':thumbsup:', body)
    body = re.sub(r'\(n\)', r':thumbsdown:', body)
    body = re.sub(r'\(i\)', r':information_source:', body)
    body = re.sub(r'\(/\)', r':white_check_mark:', body)
    body = re.sub(r'\(x\)', r':x:', body)
    body = re.sub(r'\(!\)', r':warning:', body)
    body = re.sub(r'\(\+\)', r':heavy_plus_sign:', body)
    body = re.sub(r'\(-\)', r':heavy_minus_sign:', body)
    body = re.sub(r'\(\?\)', r':grey_question:', body)
    body = re.sub(r'\(on\)', r':bulb:', body)
    body = re.sub(r'\(\*[rgby]?\)', r':star:', body)
    body = re.sub(r'\n?\|([^|]*)\|\n?(.*)', r'\n| \1 |\n| --- |\n', body)
    # Tables
    body = re.sub(r'\{panel:title=([^|]+)\|([^}]*)\}(.{4}?)([^}]*?)(.{2}?)\{panel\}', resolve_panel_group, body, flags=re.DOTALL)
    return body
data = "Accenture/Aramark issue reported for glass.endgameone.com:\r\n\r\n\"We are seeing a lot of latency with the Endgame platform. The issue is intermittent where the dashboard or investigation view will freeze up and just show a spinning wheel or present us with a \u201cFailure to Load\u201d error. I have attached some screenshots below. Time Frame: February 25, 2020 19:45 GMT - 20:30 GMT / 2:45pm EST \u2013 February 25, 2020 3:30pm EST\"\r\n\r\n!image-2020-02-25-14-41-22-559.png|width=278,height=201!\r\n\r\nThe reported time period lines up with pager duty reports seen in #sec-sre-notify\u00a0showing OOM-killer being invoked for IRIS and NATS starting at the same time.\r\n\r\n[link to Kibana logs|https://3e22da1e8243481bbda5c266cbb03f59.us-east-1.aws.found.io:9243/app/kibana#/discover?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:'2020-02-25T19:21:32.960Z',to:'2020-02-25T19:41:32.960Z'))&_a=(columns:!(message),filters:!(('$state':(store:appState),bool:(must:!((term:(log.file.path:%2Fvar%2Flog%2Fmessages)),(match:(message:oom-killer)))),meta:(alias:filter,disabled:!f,index:'filebeat-*',key:bool,negate:!f,type:custom,value:'%7B%22must%22:%5B%7B%22term%22:%7B%22log.file.path%22:%22%2Fvar%2Flog%2Fmessages%22%7D%7D,%7B%22match%22:%7B%22message%22:%22oom-killer%22%7D%7D%5D%7D'))),index:'filebeat-*',interval:auto,query:(language:kuery,query:''),sort:!(!('@timestamp',desc)))]\r\n\r\nUnknown if this is the root cause, but as part of a threat hunting activity that was scheduled for today, they were running a number of investigations at that time:\r\n\r\n!image-2020-02-25-14-40-46-103.png|width=515,height=481!"

def create():
    x = strip_description_data(data)
    #github_comments_api_url = "https://api.github.com/repos/happychander/Test_Issue/issues/10/comments"
    github_comments_api_url = "https://api.github.com/repos/happysaini/Test_issues/issues"
    session = requests.session()
    session.auth = ('')
    comment_body = {'body' : x}
    try:
        #response = session.post(github_comments_api_url, json.dumps(comment_body), verify=False)
        response = session.get(github_comments_api_url, verify=False)
        print(response)
    except:
        print("Fails")
