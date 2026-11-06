# email-assets

Public hosting for REMM email mailers, served by GitHub Pages at
https://mailermaker.github.io/email-assets/

Campaign Monitor imports each mailer from here ("Import HTML → From the web") and
copies the HTML and all images onto its own servers, so recipients never load
anything from this site.

- `images/` — the 20 brand header and footer PNGs (`<brand>-header.png`, `<brand>-footer.png`).
  The artwork masters live in SharePoint (Marketing Analytica › 1A - Email Headers & Footers);
  replace a file here under the same name to update it.
- `mailers/<campaign>/` — branded mailers, one per brand, plus `-grape` versions for
  Prop Invest and Asset Invest Group.
- `scripts/brand.py` — makes the branded mailers and checks them. Used by the
  `email-brand-wrapper` skill.

Everything here is public. Don't add anything that isn't already going out in an email.
