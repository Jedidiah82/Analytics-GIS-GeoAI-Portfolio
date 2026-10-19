"""Generate original architecture SVGs and matching PNGs. No external assets."""
from pathlib import Path
import math
import textwrap
from html import escape
from PIL import Image, ImageDraw, ImageFont

BACKGROUND = "#081522"
INK = "#ecf4fa"
MUTED = "#b2c7d8"
COLORS = {"monitoring":"#75e4c3", "aws":"#f4bf70", "azure":"#82c9ff", "cryptography":"#c9b0ff", "overview":"#75e4c3"}
DIAGRAMS = {
 "monitoring": ("Host health, made observable.", "One-shot Python checks / explicit status / optional notification", [
 ("Schedule", "Cron or a manual command invokes the same one-shot check."),
 ("Collect", "Sample CPU over an interval; inspect disk, memory and localhost."),
 ("Evaluate", "Classify threshold breaches and probe failures independently."),
 ("Report", "Write timestamped JSON and exit 0, 1, 2 or 3 for automation."),
 ("Notify, if enabled", "Use authenticated STARTTLS SMTP only when explicitly requested."),
 ("Act on the signal", "Review an alert or failed probe; keep credentials outside the code.")], "Verified: unit contracts and a real local host sample. SMTP delivery is a separate integration check."),
 "aws": ("A controlled cloud lifecycle.", "EC2 / identity checks / observable state / owned-resource cleanup", [
 ("Configure", "Select the account, region, approved image, subnet and SSH /32."),
 ("Review the plan", "Default execution prints a plan without calling AWS."),
 ("Check the boundary", "Explicit execution verifies account, SSH rules and image metadata."),
 ("Provision + persist", "Create one tagged instance with IMDSv2 and encrypted root storage."),
 ("Observe", "Wait for running state and configure a CPU alarm without email actions."),
 ("Retire owned resources", "Match account and tags; terminate, wait, then remove the run alarm.")], "Verified: offline plans and mocked lifecycle contracts. New live provisioning and cleanup are not executed."),
 "azure": ("Source to a reviewable release.", "Static HTML / validated artifact / manually dispatched deployment", [
 ("Version the source", "HTML, CSS and hosting configuration live in the project folder."),
 ("Validate the artifact", "Check structure, local assets, 404 behavior and header configuration."),
 ("Choose a release", "A manual main-branch dispatch starts the deployment job after checks."),
 ("Deploy the artifact", "A scoped repository secret supplies the Azure deployment token."),
 ("Serve through Azure", "Static Web Apps hosts the artifact and applies its configuration."),
 ("Verify the endpoint", "Check HTTPS, content, response headers and an actual missing-page 404.")], "Verified: local artifact checks. Azure deployment, response headers and public availability await live verification."),
 "cryptography": ("Trust the verification, not the file.", "Synthetic message / isolated OpenPGP keyring / positive and negative checks", [
 ("Isolate the run", "Create a new disposable GnuPG home, separate from existing keys."),
 ("Generate test keys", "Create an Ed25519 signing key and a Curve25519 encryption subkey."),
 ("Encrypt + recover", "Encrypt synthetic text, decrypt it and compare the recovered bytes."),
 ("Sign", "Produce a detached signature with a passphrase-protected test key."),
 ("Verify", "Require a valid signature status for the unchanged message."),
 ("Challenge integrity", "Modify the message; require signature verification to reject it.")], "Verified: four real GnuPG checks and offline orchestration tests. Azure Key Vault remains a separate plan."),
 "overview": ("Engineering behind the intelligence.", "Four independent labs / shared engineering discipline / inspectable evidence", [
 ("Host observability", "Monitor local resource health with explicit errors and exit states."),
 ("Cloud lifecycle", "Plan infrastructure, check boundaries and track owned resources."),
 ("Repeatable delivery", "Version, validate and deliberately release a static artifact."),
 ("Cryptographic integrity", "Recover encrypted text and reject a modified signed message."),
 ("Evidence, with scope", "Separate local tests, historical screenshots and unexecuted cloud steps."),
 ("Reproducible handover", "Publish commands, reports, architecture and file checksums.")], "These labs demonstrate complementary skills. They are not one deployed platform or a production security assessment.")
}

def draw_diagram(key, out, mobile=False):
    title, subtitle, nodes, note = DIAGRAMS[key]
    w,h = (600,2220) if mobile else (1440,920)
    image=Image.new("RGB",(w,h),BACKGROUND); d=ImageDraw.Draw(image)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle + ". " + " ".join(a+": "+b for a,b in nodes) + " " + note)}</desc><rect width="100%" height="100%" fill="{BACKGROUND}"/>']
    candidates=[(Path("C:/Windows/Fonts/segoeui.ttf"),Path("C:/Windows/Fonts/segoeuib.ttf")),(Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),(Path("/System/Library/Fonts/Supplemental/Arial.ttf"),Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"))]
    fontfile,boldfile=next(((regular,bold) for regular,bold in candidates if regular.exists() and bold.exists()),(None,None))
    accent=COLORS[key]
    def text(x,y,value,size=26,color=INK,bold=False):
        source=boldfile if bold else fontfile
        f=ImageFont.truetype(str(source),size) if source else ImageFont.load_default(size=size)
        d.text((x,y),value,font=f,fill=color)
        svg.append(f'<text x="{x}" y="{y+size*.83}" fill="{color}" font-family="Segoe UI, Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')
    def rect(x,y,cw,ch,fill="#10283b",stroke="#29465a"):
        d.rounded_rectangle((x,y,x+cw,y+ch),radius=20,fill=fill,outline=stroke,width=2)
        svg.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def arrow(a,b):
        d.line([a,b],fill=accent,width=3)
        ang=math.atan2(b[1]-a[1],b[0]-a[0]); head=[b,(b[0]-13*math.cos(ang-.5),b[1]-13*math.sin(ang-.5)),(b[0]-13*math.cos(ang+.5),b[1]-13*math.sin(ang+.5))]
        d.polygon(head,fill=accent)
        svg.append(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]}" stroke="{accent}" stroke-width="3" fill="none"/><polygon points="'+" ".join(f"{x},{y}" for x,y in head)+f'" fill="{accent}"/>')
    text(50,40,"GODWIN ETIM AKPAN / CLOUD ENGINEERING",19,accent,True)
    for i,line in enumerate(textwrap.wrap(title,25 if mobile else 60)): text(50,91+i*49,line,38 if mobile else 48,bold=True)
    sub_y=215 if mobile else 160
    for i,line in enumerate(textwrap.wrap(subtitle,37 if mobile else 100)): text(50,sub_y+i*30,line,23,MUTED)
    coords=[(50,330+i*280,500,235) for i in range(6)] if mobile else [(50,270,410,185),(515,270,410,185),(980,270,410,185),(980,535,410,185),(515,535,410,185),(50,535,410,185)]
    # The overview is a collection, not a single sequential deployed system.
    if key != "overview":
        for i in range(5):
            x,y,cw,ch=coords[i]; nx,ny,nw,nh=coords[i+1]
            if mobile or i==2: arrow((x+cw/2,y+ch+3),(nx+nw/2,ny-12))
            elif i<2: arrow((x+cw+5,y+ch/2),(nx-12,ny+nh/2))
            else: arrow((x-5,y+ch/2),(nx+nw+12,ny+nh/2))
    for i,((heading,body),(x,y,cw,ch)) in enumerate(zip(nodes,coords)):
        rect(x,y,cw,ch)
        text(x+23,y+18,f"0{i+1}",20,accent,True)
        text(x+23,y+49,heading,26 if mobile else 25,bold=True)
        for j,line in enumerate(textwrap.wrap(body,33 if mobile else 32)): text(x+23,y+92+j*(32 if mobile else 27),line,26 if mobile else 22,MUTED)
    footer=2040 if mobile else 785
    d.line((50,footer-20,w-50,footer-20),fill="#29465a",width=2)
    svg.append(f'<path d="M 50 {footer-20} H {w-50}" stroke="#29465a"/>')
    text(50,footer,"VERIFICATION BOUNDARY",18,accent,True)
    for i,line in enumerate(textwrap.wrap(note,37 if mobile else 108)): text(50,footer+36+i*28,line,22,MUTED)
    svg.append('</svg>')
    out.mkdir(parents=True,exist_ok=True)
    stem=key+('-mobile' if mobile else '')
    (out/(stem+'.svg')).write_text(''.join(svg),encoding='utf-8')
    if not mobile: image.save(out/(stem+'.png'))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("output",type=Path); a=p.parse_args()
    for key in DIAGRAMS:
        draw_diagram(key,a.output)
        draw_diagram(key,a.output,mobile=True)
