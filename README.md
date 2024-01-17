# TeZ
TeZ is quick trading app especially for scalpers and is built over the Finvasia APIs.
This project provides all necessary scripts for the app.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

For a scalper, quick entry and exit is a most useful feature required in a trading app. Scalpers generally tend to trade in 1 or 2 instruments.
Before learning scalping options, it would help to learn in a non derivative instruments such as NIFTYBEES. This app provides such a mechanism. It provides very simple gui and most of the settings are configured before the start. Further, app provides trading NIFTYBEES while the underlying instrument can be NIFTY index. 

This will be very helpful for traders that are trying to learn scalping.

In future versions, buying CE/PE options are also planned.

## Features
Following are the features

- Very simple and intuitive gui
- Uses Bracket order facility of finvasia for trading NIFTYBEES.
- Uses Websocket feed for real time updates.
- Provides mechanism such that feed can be obtained from one Finvasia a/c and trading can be done in another a/c.
- Also has feature to get the session ID from a google sheet.

## Getting Started

Finvasia SDK should be installed. For details, please ref: https://github.com/Shoonya-Dev/ShoonyaApi-py

\data\cred - contains the yml file that has all required credentials

\data\sys_cfg.yml - contains all the configurations. 

GUI_CONFIG:  
  APP_TITLE: 'TeZ - NIFTY'
  APP_GEOMETRY: '250x125'
  LONG_BUTTON: ' Buy '
  SHORT_BUTTON: 'Short'
  EXIT_BUTTON: 'Exit App'
  SQUARE_OFF_BUTTON: 'Square Off'

By updating app_geometry, size of the application window can be adjusted to suit monitor.

System has mainly 4 blocks. 

TIU - Trade interface unit. This unit provides methods for trading.
DIU - Data interface unit. This unit talks to the web socket and provides real time for display.
BKU - Book keeper unit. This gives functionality for square off mechanism.
GUI layout - Provides the user interface.

TIU configuration:

Token file - contains necessary session id in json format. If you do not have other session, then make this as null.
cred file - client_id.yml needs to updated with all credentials and api keys.

If you are using TIU and DIU from the same a/c, then  SAVE_TOKEN_FILE_CFG: should be 'YES' and SAVE_TOKEN_FILE_NAME: 
should be a json file.

TIU:
  USE_GSHEET_TOKEN: 'NO' #YES NO
  GOOGLE_SHEET:
    CLIENT_SECRET: null
    URL: null
    NAME: null
  TOKEN_FILE: './log/tarak_token.json'
  CRED_FILE:  './log/client_id.yml' 

  EXCHANGE: 'NSE'             #valid values : NSE 
  INSTRUMENT: 'NIFTYBEES'     #valid values : NIFTYBEES 
  EXPIRY_DATE: null           #Format: 11JAN24
  
  CE_STRIKE_OFFSET: 0         # 0 means ATM,   1 is OTM, -1 means ITM
  PE_STRIKE_OFFSET: 0         # 0 means ATM,  -1 is OTM, +1 means ITM

  PROFIT_PER: 0.4
  STOPLOSS_PER: 0.2

  PRODUCT: 'MIS'
  USE_OCO: 'YES'       # 'YES' 'NO'
  QUANTITY: 1
  N_LEGS: 1            # Future USE,  ice berg orders
  TRADE_MODE: 'LIVE'  #'LIVE'
  TRADES_RECORD_FILE: 'F:/Python_log/tiny_tez/orders.csv'
  SAVE_TOKEN_FILE_CFG: 'NO'   #YES NO
  SAVE_TOKEN_FILE_NAME: null

DIU configuration:
If TIU is generating a token file, then the DIU should use that token file so that same session is shared 
between TIU and DIU.

DIU:
  GOOGLE_SHEET:
    CLIENT_SECRET: null
    URL: null
    NAME: null
  TOKEN_FILE: null
  CRED_FILE: ''
  UL_INSTRUMENT: 'NIFTY'   #Not used.. hard coded in the system
  EXPIRY_DATE: null
  EXCHANGE: 'NSE'
  SAVE_TOKEN_FILE_CFG: 'NO'   #YES NO
  SAVE_TOKEN_FILE_NAME: null   #Full Path to json file 

System configuration:
Log file gives the path of the file where log file is to be generated.
DL_FOLDER: 'F:/Python_log/tiny_tez' is where intermediate files such as downloaded symbol files are stored.

SYSTEM:
  LOG_FILE: 'F:/Python_log/tiny_tez/app.log'
  DL_FOLDER: 'F:/Python_log/tiny_tez'
  MARKET_TIMING: 
    OPEN: "09:15"   #Zero padded
    CLOSE: "15:30"
  SQ_OFF_TIMING: "15:19"  #Future Use
  TELEGRAM:          #Future Use
    NOTIFY : "OFF"  #Notifier is created but only the notifications are not pushed by this control parameter.
    CFG_FILE: null

### Installation

Step-by-step guide on how to install.

```bash
# Example installation steps
git clone https://github.com/tarakbluru/TeZ.git
cd TeZ

#To Run:
python tez_main.py