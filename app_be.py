"""
File: app_be.py
Author: [Tarakeshwar NC]
Date: January 15, 2024
Description: This is the backend service provider for the gui.
"""
# Copyright (c) [2024] [Tarakeshwar N.C]
# This file is part of the TeZ project.
# It is subject to the terms and conditions of the MIT License.
# See the file LICENSE in the top-level directory of this distribution
# for the full text of the license.

__app_name__ = 'TeZ'
__author__ = "Tarakeshwar N.C"
__copyright__ = "2024"
__date__ = "2024/1/14"
__deprecated__ = False
__email__ = "tarakesh.nc_at_google_mail_dot_com"
__license__ = "MIT"
__maintainer__ = "Tarak"
__status__ = "Development"

import sys
import traceback

import app_utils as utils

logger = utils.get_logger(__name__)

try:
    import copy
    import json
    import math
    from datetime import datetime
    from threading import Timer

    import app_mods
    import numpy as np
    import yaml

except Exception as e:
    logger.debug(traceback.format_exc())
    logger.error(("Import Error " + str(e)))
    sys.exit(1)


class TeZ_App_BE:
    def __init__(self):
        def create_tiu():
            cred_file = app_mods.get_system_info("TIU", "CRED_FILE")
            logger.info(f'credfile{cred_file}')

            with open(cred_file) as f:
                cred = yaml.load(f, Loader=yaml.FullLoader)

            session_id = None

            if app_mods.get_system_info("TIU", "USE_GSHEET_TOKEN") == 'YES':
                gsheet_info = app_mods.get_system_info("TIU", "GOOGLE_SHEET")
                print(gsheet_info)
                gsheet_client_json = gsheet_info['CLIENT_SECRET']
                url = gsheet_info['URL']
                sheet_name = gsheet_info['NAME']
                if gsheet_client_json != '' and url != '' and sheet_name != '':
                    session_id = app_mods.get_session_id_from_gsheet(
                                            cred,
                                            gsheet_client_json=gsheet_client_json,
                                            url=url,
                                            sheet_name=sheet_name
                                        )

            dl_filepath = app_mods.get_system_info("SYSTEM", "DL_FOLDER")
            logger.info(f'dl_filepath: {dl_filepath}')

            tiu_token_file = app_mods.get_system_info("TIU", "TOKEN_FILE")
            logger.info(f'token_file: {tiu_token_file}')

            tiu_cred_file = app_mods.get_system_info("TIU", "CRED_FILE")

            tiu_save_token_file_cfg = app_mods.get_system_info("TIU", "SAVE_TOKEN_FILE_CFG")
            tiu_save_token_file = app_mods.get_system_info("TIU", "SAVE_TOKEN_FILE_NAME")

            tcc = app_mods.Tiu_CreateConfig(tiu_cred_file,
                                            session_id,
                                            tiu_token_file,
                                            False,
                                            dl_filepath,
                                            None,
                                            tiu_save_token_file_cfg,
                                            tiu_save_token_file)
            logger.debug(f'tcc:{str(tcc)}')
            tiu = app_mods.Tiu(tcc=tcc)

            logger.info('Creating dataframe for quick access')
            instruments = app_mods.get_system_info("TIU", "INSTRUMENT_INFO")

            symbol_exp_date_pairs = []
            for symbol, info in instruments.items():
                logger.debug(f"Instrument: {symbol}")
                if info['EXCHANGE'] == 'NFO':
                    symbol = info['SYMBOL']
                    exp_date = info['EXPIRY_DATE']
                    symbol_exp_date_pairs.append((symbol, exp_date))

            if len(symbol_exp_date_pairs):
                tiu.compact_search_file(symbol_exp_date_pairs)

            tiu.create_sym_token_tsym_q_access(symbol_list=None, instruments=instruments)

            return tiu

        def create_diu():
            diu_cred_file = app_mods.get_system_info("DIU", "CRED_FILE")
            diu_token_file = app_mods.get_system_info("DIU", "TOKEN_FILE")
            logger.info(f'token_file: {diu_token_file}')
            diu_save_token_file_cfg = app_mods.get_system_info("DIU", "SAVE_TOKEN_FILE_CFG")
            diu_save_token_file = app_mods.get_system_info("DIU", "SAVE_TOKEN_FILE_NAME")

            dcc = app_mods.Diu_CreateConfig(diu_cred_file, None, diu_token_file, False, None, None, diu_save_token_file_cfg, diu_save_token_file)
            logger.debug(f'dcc:{str(dcc)}')
            diu = app_mods.Diu(dcc=dcc)

            diu.ul_symbol = app_mods.get_system_info("GUI_CONFIG", "RADIOBUTTON_DEF_VALUE")

            return diu

        def create_bku():
            bku_file = app_mods.get_system_info("TIU", "TRADES_RECORD_FILE")
            bku = app_mods.BookKeeperUnit(bku_file, reset=False)
            return bku

        self.tiu = create_tiu()
        self.diu = create_diu()
        self.bku = create_bku()

        self._sqoff_time = None
        self.sqoff_timer = None

        auto_sq_off_time_str = app_mods.get_system_info("SYSTEM", "SQ_OFF_TIMING")
        current_time = datetime.now().time()
        logger.info(f'auto_sq_off_time:{auto_sq_off_time_str} current_time:  {current_time}')
        hr = datetime.strptime(auto_sq_off_time_str, '%H:%M').hour
        minute = datetime.strptime(auto_sq_off_time_str, '%H:%M').minute
        self._sq_off_time = datetime.now().replace(hour=hr, minute=minute, second=0, microsecond=0)

        rm_durn = utils.calcRemainingDuration(self._sq_off_time.hour, self._sq_off_time.minute)
        if (rm_durn > 0):
            self.sqoff_timer = Timer(rm_durn, self.__square_off_position_timer__)
        if self.sqoff_timer is not None:
            self.sqoff_timer.name = "SQ_OFF_TIMER"
            self.sqoff_timer.daemon = True
            self.sqoff_timer.start()
        else:
            logger.debug("Square off Timer Is not Created.. as Time has elapsed ")

    def __square_off_position_timer__(self):
        logger.info(f'{datetime.now().time()} !! Auto Square Off Time !!')
        self.square_off_position(mode='ALL')

    @property
    def ul_symbol(self):
        return self.diu.ul_symbol

    @ul_symbol.setter
    def ul_symbol(self, ul_symbol):
        self.diu.ul_symbol = ul_symbol

    def exit_app_be(self):
        if self.sqoff_timer is not None:
            if self.sqoff_timer.is_alive():
                self.sqoff_timer.cancel()

    @staticmethod
    def get_instrument_info(exchange, ul_inst):
        instruments = app_mods.get_system_info("TIU", "INSTRUMENT_INFO")
        instrument_info = None
        for inst_id, info in instruments.items():
            logger.debug(f"Instrument: {inst_id}")
            if info['EXCHANGE'] == exchange and info['UL_INSTRUMENT'] == ul_inst:
                instrument_info = info
                break
        return instrument_info  # symbol, exp_date, ce_offset, pe_offset

    def market_action(self, action):
        def get_tsym_token(tiu: app_mods.Tiu, diu: app_mods.Diu, action: str):
            ul_sym = diu.ul_symbol
            exch = app_mods.get_system_info("TIU", "EXCHANGE")
            inst_info = TeZ_App_BE.get_instrument_info(exch, ul_sym)
            sym = inst_info['SYMBOL']
            expiry_date = inst_info['EXPIRY_DATE']
            ce_offset = inst_info['CE_STRIKE_OFFSET']
            pe_offset = inst_info['PE_STRIKE_OFFSET']

            logger.debug(f'{ul_sym} : {exch} {sym} {expiry_date}')
            qty = round(app_mods.get_system_info("TIU", "QUANTITY"), 0)
            ltp = diu.get_latest_tick()
            if exch == 'NFO':
                # find the nearest strike price
                strike_diff = inst_info['STRIKE_DIFF']
                strike1 = int(math.floor(ltp / strike_diff) * strike_diff)
                strike2 = int(math.ceil(ltp / strike_diff) * strike_diff)
                strike = strike1 if abs(ltp - strike1) < abs(ltp - strike2) else strike2
                logger.debug(f'strike1: {strike1} strike2: {strike2} strike: {strike}')
                c_or_p = 'C' if action == 'Buy' else 'P'

                if c_or_p == 'C':
                    strike_offset = ce_offset
                else:
                    strike_offset = pe_offset

                strike += int(strike_offset * strike_diff)
                # expiry_date = app_mods.get_system_info("TIU", "EXPIRY_DATE")
                parsed_date = datetime.strptime(expiry_date, '%d-%b-%Y')
                exp_date = parsed_date.strftime('%d%b%y')
                searchtext = f'{sym}{exp_date}{c_or_p}{strike:.0f}'
            elif exch == 'NSE':
                searchtext = sym
                strike = None
                logger.debug(f'ltp:{ltp} strike:{strike}')
            else:
                ...

            logger.info(f'exch: {exch} searchtext: {searchtext}')
            token, tsym = tiu.search_scrip(exchange=exch, symbol=searchtext)
            ltp, ti, ls = tiu.fetch_ltp(exch, token)
            qty = qty * ls

            r = tiu.get_security_info(exchange=exch, symbol=tsym, token=token)
            logger.debug(f'{json.dumps(r, indent=2)}')
            frz_qty = None
            if isinstance(r, dict) and 'frzqty' in r:
                frz_qty = int(r['frzqty'])
            else:
                frz_qty = qty+1

            # Ideally, for breakout orders need to use the margin available
            # For option buying it is cash availablity.
            # To keep it simple, using available cash for both.
            margin = self.tiu.avlble_margin
            if margin < (ltp * 1.1 * qty):
                old_qty = qty
                qty = math.floor(margin/(1.1*ltp))  # 10% buffer
                qty = int(qty/ls)*ls  # Important as above value will not be a multiple of lot
                logger.info(f'Available Margin: {self.tiu.avlble_margin:.2f} Required Amount: {ltp * old_qty} Updating qty: {old_qty} --> {qty} ')

            logger.info(f'''strike: {strike}, sym: {sym}, tsym: {tsym}, token: {token},
                        qty:{qty}, ltp: {ltp}, ti:{ti} ls:{ls} frz_qty: {frz_qty} lot-size: {ls}''')

            return strike, sym, tsym, token, qty, ltp, ti, frz_qty, ls

        strike, sym, tsym, token, qty, ltp, ti, frz_qty, ls = get_tsym_token(self.tiu, self.diu, action=action)
        oco_order = np.NaN
        os = app_mods.shared_classes.OrderStatus()
        status = app_mods.Tiu_OrderStatus.HARD_FAILURE

        given_nlegs = app_mods.get_system_info("TIU", "N_LEGS")
        if not given_nlegs:
            given_nlegs = 1

        if qty > 0:
            if qty < frz_qty:
                # divide order into per_leg_qty = int (qty/nlegs)
                # residual_qty = qty - per_leg_qty*nlegs
                # Create order list
                # Place multi_orders
                # per_leg_qty = math.floor(qty/nlegs/ls)*ls
                # logger.info(f'qty {qty} < {frz_qty} nlegs:{nlegs} per_leg_qty: {per_leg_qty}')
                # if per_leg_qty == 0.0:
                #     per_leg_qty = qty
                #     nlegs = 1
                min_nlegs = math.floor(qty/frz_qty)
                extra_leg = 1 if (qty % frz_qty) else 0
                logger.info(f'qty {qty} < {frz_qty} given_nlegs : {given_nlegs} min_nlegs:{min_nlegs} extra_leg: {extra_leg}')
                if given_nlegs > (min_nlegs + extra_leg):
                    per_leg_qty = math.floor(qty/(given_nlegs*ls))*ls
                    nlegs = given_nlegs - extra_leg
                else:
                    nlegs = min_nlegs
                    per_leg_qty = 0
                    if nlegs:
                        per_leg_qty = (frz_qty-1) if nlegs else math.floor(qty/nlegs/ls)*ls
                logger.info(f'nlegs: {given_nlegs} --> {nlegs} extra_leg: {extra_leg}')
            else:
                min_nlegs = math.floor(qty/frz_qty)
                extra_leg = 1 if (qty % frz_qty) else 0
                logger.info(f'qty {qty} > {frz_qty} given_nlegs: {given_nlegs} min_nlegs:{min_nlegs} extra_leg: {extra_leg}')
                if given_nlegs > (min_nlegs + extra_leg):
                    per_leg_qty = math.floor(qty/given_nlegs/ls)*ls
                    nlegs = given_nlegs - extra_leg
                else:
                    logger.info(f'nlegs: {given_nlegs} --> {min_nlegs} extra_leg: {extra_leg}')
                    nlegs = min_nlegs
                    per_leg_qty = (frz_qty-1) if nlegs else math.floor(qty/nlegs/ls)*ls
            rem_qty = (qty - nlegs * per_leg_qty)
            logger.info(f'Placing nlegs: {nlegs} per_leg_qty:{per_leg_qty} residual: {rem_qty}')

        else:
            logger.info(f'qty: {qty} is not allowed')
            return

        logger.info(f'sym:{sym} tsym:{tsym} ltp: {ltp}')
        use_gtt_oco = True if app_mods.get_system_info("TIU", "USE_GTT_OCO").upper() == 'YES' else False
        remarks = None

        ul_inst = self.diu.ul_symbol
        exch = app_mods.get_system_info("TIU", "EXCHANGE")
        inst = TeZ_App_BE.get_instrument_info(exchange=exch, ul_inst=ul_inst)
        orders = []
        if (sym == 'NIFTYBEES' or sym == 'BANKBEES') and ltp is not None:
            pp = inst["PROFIT_PER"] / 100.0
            sl_p = inst["STOPLOSS_PER"] / 100.0
            if not use_gtt_oco:
                bp = utils.round_stock_prec(ltp * pp, base=ti)
                bl = utils.round_stock_prec(ltp * sl_p, base=ti)
                logger.debug(f'ltp:{ltp} pp:{pp} bp:{bp} sl_p:{sl_p} bl:{bl}')

                if per_leg_qty:
                    if action == 'Buy':
                        order = app_mods.BO_B_MKT_Order(tradingsymbol=tsym,
                                                        quantity=per_leg_qty, book_loss_price=bl,
                                                        book_profit_price=bp, bo_remarks=remarks)
                    else:
                        order = app_mods.BO_S_MKT_Order(tradingsymbol=tsym,
                                                        quantity=per_leg_qty, book_loss_price=bl,
                                                        book_profit_price=bp, bo_remarks=remarks)
                    # deep copy is not required as object contain same info and are not
                    # modified
                    orders = [copy.deepcopy(order) for _ in range(nlegs)]

                if rem_qty:
                    if action == 'Buy':
                        order = app_mods.BO_B_MKT_Order(tradingsymbol=tsym,
                                                        quantity=rem_qty, book_loss_price=bl,
                                                        book_profit_price=bp, bo_remarks=remarks)
                    else:
                        order = app_mods.BO_S_MKT_Order(tradingsymbol=tsym,
                                                        quantity=rem_qty, book_loss_price=bl,
                                                        book_profit_price=bp, bo_remarks=remarks)
                    orders.append(order)
            else:
                bp1 = utils.round_stock_prec(ltp+pp*ltp, base=ti)
                bp2 = utils.round_stock_prec(ltp-pp*ltp, base=ti)
                bp = bp1 if action == 'Buy' else bp2

                bl1 = utils.round_stock_prec(ltp-sl_p*ltp, base=ti)
                bl2 = utils.round_stock_prec(ltp+sl_p*ltp, base=ti)

                bl = bl1 if action == 'Buy' else bl2
                logger.debug(f'ltp:{ltp} pp:{pp} bp:{bp} sl_p:{sl_p} bl:{bl}')

                if per_leg_qty:
                    if action == 'Buy':
                        order = app_mods.shared_classes.Combi_Primary_B_MKT_And_OCO_S_MKT_I_Order_NSE(tradingsymbol=tsym, quantity=per_leg_qty,
                                                                                                      bl_alert_p=bl, bp_alert_p=bp,
                                                                                                      remarks=remarks)
                    else:
                        order = app_mods.shared_classes.Combi_Primary_S_MKT_And_OCO_B_MKT_I_Order_NSE(tradingsymbol=tsym, quantity=per_leg_qty,
                                                                                                      bl_alert_p=bl, bp_alert_p=bp,
                                                                                                      remarks=remarks)
                    # deep copy is not required as object contain same info and are not
                    # modified
                    orders = [copy.deepcopy(order) for _ in range(nlegs)]

                if rem_qty:
                    if action == 'Buy':
                        order = app_mods.shared_classes.Combi_Primary_B_MKT_And_OCO_S_MKT_I_Order_NSE(tradingsymbol=tsym, quantity=rem_qty,
                                                                                                      bl_alert_p=bl, bp_alert_p=bp,
                                                                                                      remarks=remarks)
                    else:
                        order = app_mods.shared_classes.Combi_Primary_S_MKT_And_OCO_B_MKT_I_Order_NSE(tradingsymbol=tsym, quantity=rem_qty,
                                                                                                      bl_alert_p=bl, bp_alert_p=bp,
                                                                                                      remarks=remarks)
                    orders.append(order)
        else:
            if use_gtt_oco:
                pp = inst["PROFIT_POINTS"]
                bp = utils.round_stock_prec(ltp+pp, base=ti)

                sl_p = inst["STOPLOSS_POINTS"]
                bl = utils.round_stock_prec(ltp-sl_p, base=ti)
                logger.debug(f'ltp:{ltp} pp:{pp} bp:{bp} sl_p:{sl_p} bl:{bl}')
            else:
                bp = bl = None

            if per_leg_qty:
                order = app_mods.shared_classes.Combi_Primary_B_MKT_And_OCO_S_MKT_I_Order_NFO(tradingsymbol=tsym, quantity=per_leg_qty,
                                                                                              bl_alert_p=bl, bp_alert_p=bp,
                                                                                              remarks=remarks)
                orders = [copy.deepcopy(order) for _ in range(nlegs)]

            if rem_qty:
                order = app_mods.shared_classes.Combi_Primary_B_MKT_And_OCO_S_MKT_I_Order_NFO(tradingsymbol=tsym, quantity=rem_qty,
                                                                                              bl_alert_p=bl, bp_alert_p=bp,
                                                                                              remarks=remarks)
                orders.append(order)

        if len(orders):
            for i, order in enumerate(orders):
                try:
                    if isinstance(order, app_mods.shared_classes.BO_B_MKT_Order) or isinstance(order, app_mods.shared_classes.BO_S_MKT_Order):
                        remarks = f'TeZ_{i+1}_Qty_{order.quantity:.0f}_of_{qty:.0f}'
                    else:
                        remarks = f'TeZ_{i+1}_Qty_{order.primary_order_quantity:.0f}_of_{qty:.0f}'
                    # logger.info(remarks)
                    order.remarks = remarks
                    # logger.info(f'order: {i} -> {order}')
                except Exception:
                    logger.error(traceback.format_exc())

            resp_exception, resp_ok, os_tuple_list = self.tiu.place_and_confirm_tez_order(orders=orders, use_gtt_oco=use_gtt_oco)
            if resp_exception:
                logger.info('Exception had occured while placing order: ')
            if resp_ok:
                logger.debug(f'respok: {resp_ok}')

        symbol = tsym + '_' + str(token)

        total_qty = 0
        for stat, os in os_tuple_list:
            status = stat.name
            order_time = os.fill_timestamp
            order_id = os.order_id
            qty = os.fillshares
            total_qty += qty
            oco_order = None
            for order in orders:
                if order_id == order.order_id:
                    oco_order = order.al_id
                    break
            self.bku.save_order(order_id, symbol, qty, order_time, status, oco_order)

        logger.info(f'Total Qty taken : {total_qty}')
        self.bku.show()

        return

    def square_off_position(self, mode='SELECT'):
        df = self.bku.fetch_order_id()
        if mode == 'ALL':
            self.tiu.square_off_position(df=df)
        else:
            exch = app_mods.get_system_info("TIU", "EXCHANGE")
            ul_sym = self.diu.ul_symbol
            inst_info = TeZ_App_BE.get_instrument_info(exch, ul_sym)
            sq_off_symbol = inst_info['SYMBOL']
            logger.info(f'Sq_off_symbol:{sq_off_symbol}')
            self.tiu.square_off_position(df=df, symbol=sq_off_symbol)

        print("Square off Position - Complete.")

    def data_feed_connect(self):
        self.diu.connect_to_data_feed_servers()

    def data_feed_disconnect(self):
        self.diu.disconnect_data_feed_servers()

    def get_latest_tick(self):
        return self.diu.get_latest_tick()
