import os
import discord
import requests
import textwrap
import mimetypes

from io import BytesIO
from wand.image import Image
from discord.ext import commands
from dotenv import load_dotenv
from PIL import ImageDraw, ImageFont
from PIL import Image as PILImage

#login as the bot without giving away token on github
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#image types accepted for image captioning
SUPPORTED_MIMETYPES = ["image/jpeg", "image/png", "image/webp"]

#set the prefix used for all commands to communicate with the bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

#function to download the image to temp.png so it can be modified
def download_image(ctx):
    image_url = ctx.message.attachments[0].url
    response = requests.get(image_url)
    file = open("temp.png", "wb")
    file.write(response.content)
    file.close()

def caption_image(image_file, caption, font="GentiumAlt-R.ttf"):
    img = PILImage.open(image_file)
    draw = ImageDraw.Draw(img)
    font_size = int(img.width/16)
    font = ImageFont.truetype(font, font_size)
    caption_w, caption_h = draw.textsize(caption, font=font)
    
    draw.text(((img.width-caption_w)/2, (img.height-caption_h)/8), #position
              caption, #text
              (255,255,255), #color
              font=font, #font
              stroke_width=2, #text outline width
              stroke_fill=(0,0,0)) #text outline color

    with BytesIO() as img_bytes:
        img.save(img_bytes, format=img.format)
        content = img_bytes.getvalue()
    
    return content



#simple indicator that the bot is functioning
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.command(name="pixels")
async def pixels(ctx):
    if not ctx.message.attachments:
        await ctx.message.reply("Please attach an image for me to read.")
        return

    download_image(ctx)

    width, height = 0, 0.0

    with Image(filename="temp.png") as image:
        #enforce pixels' quantum between 0 and 255
        image.depth = 8
        width, height = image.width, image.height
        blob = image.make_blob(format="RGB")

    pixels = {}

    #collect pixels and count them
    for cursor in range(0, width * height):
        pixel = str(blob[cursor]) +  '.' + str(blob[cursor + 1]) + '.' + str(blob[cursor + 2])
        if pixel in pixels:
            pixels[pixel] += 1
        else:
            pixels[pixel] = 1

    #get the most commonly occuring pixel
    mostCommonPixel = "0.0.0"
    mostCommonPixelCount = -1
    for pixel, count in pixels.items():
        if count > mostCommonPixelCount:
            mostCommonPixel = pixel
            mostCommonPixelCount = count

    #make a web request to obtain information about the most commonly occuring pixels
    rgb = mostCommonPixel.split(".")
    r = requests.get("https://www.thecolorapi.com/id?rgb=rgb(" + rgb[0] + ',' + rgb[1] + ',' + rgb[2])
    j = r.json()

    #provide the user with the results from the json
    await ctx.message.reply("Closest Name: " + j["name"]["value"] + '\n' + \
    "Closest Hex: " + j["name"]["closest_named_hex"] + '\n' + \
    "Exact Match: " + ("Yes" if j["name"]["exact_match_name"] == "true" else "No") \
    )

@bot.command(name="blur")
async def blur(ctx, arg="3"):
    if not ctx.message.attachments:
        await ctx.message.reply("Please attach an image for me to read.")
        return

    download_image(ctx)
    
    with Image(filename="temp.png") as image:
        image.blur(sigma=int(arg))
        image.save(filename="temp.png")

    await ctx.message.reply(file=discord.File("temp.png"))


@bot.command(name="rotate")
async def rotate(ctx, arg=180):
    if not ctx.message.attachments:
        await ctx.message.reply("Please attach an image for me to read.")
        return

    download_image(ctx)

    with Image(filename="temp.png") as image:
        image.rotate(arg)
        image.save(filename="temp.png")

    await ctx.message.reply(file=discord.File("temp.png"))

@bot.command(name="search")
async def search(ctx):
    if not ctx.message.attachments:
        await ctx.message.reply("Please attach an image for me to read.")
        return

    download_image(ctx)

    #generate a google lens search url
    search_url = "http://www.google.hr/searchbyimage/upload" 
    multipart = {"encoded_image": ("temp.png", open("temp.png", "rb")), "image_content": ''}
    r = requests.post(search_url, files=multipart, allow_redirects=False)
    #provide the user with a helpful link to the data
    #may want to simulate a browser to read the html page to provide more data in Discord
    await ctx.message.reply(r.headers["Location"])

@bot.command(name="caption")
async def caption(ctx, *, caption_text):
    if not caption_text:
        await ctx.message.reply("Please include some caption text after the `!caption` command. For example `!caption \"Hello world!\"")
        return
    elif not ctx.message.attachments:
        await ctx.message.reply("Please attach an image for me to read.")
        return
    image_url = ctx.message.attachments[0].url
    if mimetypes.guess_type(image_url)[0] not in SUPPORTED_MIMETYPES:
        await ctx.message.reply("Sorry, the file you attached is not a supported image format. Please upload a PNG, JPEG or WebP image.")
        return

    r = requests.get(image_url)
    image_filename = ctx.message.attachments[0].filename
    final_image = caption_image(BytesIO(r.content), caption_text)
    await ctx.message.reply(file=discord.File(BytesIO(final_image), filename=f"captioned-{image_filename}"))

bot.run(DISCORD_TOKEN)
