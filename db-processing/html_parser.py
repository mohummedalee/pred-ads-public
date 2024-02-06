"""
on a high level, process the html to find:
given html column from DB, return:
- ad caption (text on top)
- link (the public-facing version)
- URL
- link description (bold)
- link caption (small, greyed out)

running notes:
- text after URL is link caption
- text before URL is bolded link description
"""
from urllib import parse
import re
from selectolax.parser import HTMLParser
import pdb

CTA_LIST = ['Apply Now', 'Book Now', 'Buy Tickets', 'Call Now', 'Contact Us',
    'Donate Now', 'Get Directions', 'Download', 'Get Offer', 'Get Quote', 'Get Showtimes', 'Install Now',
    'Learn More', 'Like Page', 'Listen Now', 'Open Link', 'Order Now', 'Play Game', 'Request Time', 'Save', 'See Menu',
    'Send Message', 'Send WhatsApp Message','Shop Now','Sign Up','Subscribe','Use App','View Event','Watch More']

def partial_match(result_set, current):
    for s in result_set:
        if current in s:
            return True

    return False

class DBHTMLParser():
    def __init__(self, html):
        parser = HTMLParser(html)
        self.text_elements = parser.css(r'[dir="auto"]')
        self.links = parser.css('a')
        # terminology: link = user-facing, url = web url
        self.link_ind = None        
        self.url = None
        self.cta = ''

        # important to set this as soon as parser is initialized
        self.publicLink()
        if not self.link_ind:
            self.is_image_ad = False
        else:
            self.is_image_ad = True


    def publicLink(self):
        # regex from: https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
        link_re = "((https?:\/\/(?:www\.|(?!www)))?[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
        for i, el in enumerate(self.text_elements):
            if re.match(link_re, el.text()):
                self.link_ind = i
                break


    def callToAction(self):
        cta_list = CTA_LIST
        
        if not self.link_ind:
            return

        # iterate from end until like, comment, share runs out
        # for i in range(len(self.text_elements)-1, self.link_ind, -1):
        #     el = self.text_elements[i]
        #     p1 = '[\d]* Share(s)?'
        #     p2 = '[\d]* Like(s)?'
        #     p3 = '[\d]* Comment(s)?'
        #     if el.text() not in ['Like', 'Comment', 'Share'] and \
        #     not re.match(p1, el.text()) and not re.match(p2, el.text()) and not re.match(p3, el.text()):
        #         self.cta = el.text()
        #         break

        for el in self.text_elements:
            if el.text() in cta_list:
                self.cta = el.text()
                break


    def linkedURL(self):
        # different from the pretty public facing URL, fetch the pointed URL
        for el in self.links[::-1]:
            # starting links point to page, later links point to webpage, so traversing backwards
            if 'href' in el.attributes:
                cand = parse.unquote(el.attributes['href'])
                referral = cand.split('l.php?u=')[-1]   # chop off FB referral
                # chop off remaining FB params
                url = referral.split('?fbclid')[0]
                # print(url)
                self.url = url
                break



    def linkDescriptionCaption(self):
        """
        the first child of par Node (which is a div) is the public link
        the second child contains both the link description (bold) and the link caption (grey)
        all the following brittle parsing jujitsu is built around this insight
        """
        if not self.is_image_ad:            
            return
        try:
            el = self.text_elements[self.link_ind]
            par = el.parent.parent
            seq = par.iter()
            divs = [x for x in seq]
            link_desc_div = divs[1].css_first('div')    # contains both bold description and greyed caption
            inner_elems = link_desc_div.css('[dir="auto"]')
            
            self.link_desc = inner_elems[0].text()
            
            caption_text_set = set([])  # there might be duplicates here
            self.link_caption = ''
            # index 1 element is a repeat because of two spans with dir=auto
            for el in inner_elems[2:]:
                caption_text_set.add(el.text())
            self.link_caption = ' '.join(caption_text_set)
        except:
            self.link_caption = ''
            self.link_desc = ''

    def adCaption(self, advertiser):
        # remove all duplicates from ad caption, repeats may occur due to dir=auto selection
        caption = set([])
        # "Sponsored", but with random letters in-between
        # fb_is_evil = '.*[^ ]*S[^ ]*p[^ ]*o[^ ]*n[^ ]*s[^ ]*o[^ ]*r[^ ]*e[^ ]*d[^ ].*'
        fb_is_evil = '.*S.*p.*o.*n.*s.*o.*r.*e.*d.*'

        for el in self.text_elements[:self.link_ind]:
            text = el.text().strip()
            if text != advertiser and not re.match(fb_is_evil, text) and not partial_match(caption, text)\
                and all(["Sponsored" not in text, "Paid for by" not in text, "About this ad" not in text, "Confirmed Organization" not in text]):
                caption.add(text)
                if "see more" in text[-10:].lower():
                    # stop processing if See more is encountered
                    break

        self.caption = '\n'.join(list(caption))

    def cleanupMessage(self, message, advertiser):
        # Helpful for cleaning up the "message" column in the ads table
        fb_is_evil = ".*S.*p.*o.*n.*s.*o.*r.*e.*d.*"
        patterns = [x.lower() for x in CTA_LIST] + ["like", "comment", "share", "paid for by", "about this ad", "confirmed organization"]
        
        cleaned = set([])   # deduplicated message
        for el in message.split('\n'):
            text = el.strip()
            # pdb.set_trace()
            if text != advertiser and not partial_match(cleaned, text) and '----' not in text\
                 and not re.match(fb_is_evil, text) and not any([pat in text.lower() for pat in patterns]):
                # pdb.set_trace()
                cleaned.add(text)
                if "see more" in text[-10:].lower():
                    break

        # pdb.set_trace()
        return '\n'.join(list(cleaned))


if __name__ == '__main__':
    # for testing etc.
    with open('example/div.html', 'r') as fh:
        div = fh.read()

    parser = DBHTMLParser(div)
    parser.callToAction()
    parser.linkedPage()    
