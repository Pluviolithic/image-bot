import os
import discord
import requests

from wand.image import Image
from discord.ext import commands
from dotenv import load_dotenv

#login as the bot without giving away token on github
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#set the prefix used for all commands to communicate with the bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

#function to download the image to temp.png so it can be modified
def download_image(ctx):
    image_url = ctx.message.attachments[0].url
    response = requests.get(image_url)
    file = open("temp.png", "wb")
    file.write(response.content)
    file.close()

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
        image.blur(radius=0, sigma=int(arg))
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

bot.run(DISCORD_TOKEN)
