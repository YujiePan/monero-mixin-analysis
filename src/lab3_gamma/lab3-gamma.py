# -*- coding: utf-8 -*-
# @Author: Yujie Pan
# @Date:   2018-05-30 11:37:19
# @Last Modified by:   Yujie Pan
# @Last Modified time: 2018-05-31 02:44:01


import sqlite3
import os
import math
import sys
import time
import random
import datetime
from scipy.stats import gamma
sys.path.append("..")
from db_builder import db_block_time_stamp
BLOCK_TIME = db_block_time_stamp.init()


SIZE_DB = [0, 32929106, 33036408, 32872161, 32784690]
MIX_SIZE = 0
SIMU_TIMES = 250
ALPHA = 13.19
BETA = 0.86
D = gamma(ALPHA, scale=1 / BETA)


def main():
    try:
        th = int(sys.argv[1])
        mix = int(sys.argv[2])
    except:
        th = int(input("THREAD: "))
        mix = int(input("MIXINS: "))
    mix_size = mix
    info = simulate(th, mix, SIZE_DB[th],  SIMU_TIMES)
    write_log(
        th, "../../result/lab3-th{}-mix{}.txt".format(th, mix_size), info)


def write_log(i, name, content):
    with open(name, "a") as f:
        f.write("[{}] TH{}: {}\r\n".format(
            timestamp2string(time.time()), i, content))


def line_txto_txfrom_nfrom(cur, random_num):
    cur.execute("SELECT * FROM tx_in_out LIMIT 1 OFFSET {};".format(random_num))
    for item in cur.fetchall():
        return item[0:3]
    return 0, 0, 0


def block_minitxid_via_txid(cur, tx, n):
    cur.execute("SELECT * FROM TXTOBLOCK WHERE txid = {};".format(tx))
    for item in cur.fetchall():
        return item[1], item[2] + n
    return 3, 3


def block_via_minitxid(cur, mini_id):
    cur.execute(
        "SELECT * FROM TXTOBLOCK WHERE MINITX_STARTING <= {} ORDER BY block desc LIMIT 1;".format(
            mini_id))
    for item in cur.fetchall():
        return item[1]


def get_time_stamp(block, mini_id):
    return random.randint(BLOCK_TIME[block - 1], BLOCK_TIME[block])


def disp_progress(start_time, start_p, now_p, end_p, comment):
    try:
        print("=" * 20, "\nREADY:\t", comment)
        pct = (now_p - start_p) / (end_p - start_p)
        used_time = time.time() - start_time
        print("COST TIME:\t", used_time // 60, ' min\t= ', used_time, " s")
        print("REMAINING:\t", used_time / (pct + 1e-10) * (1 - pct + 1e-10) //
              60, ' min\t= ', used_time / (pct + 1e-10) * (1 - pct + 1e-10), " s")
    except:
        pass


def simulate(thread_id, MIX, max_random,  SIMU_TIMES):
    t1 = time.time()  # get current time

    DB_TX_IN_OUT_PATH = "../../db/new_tx_in_out{}.sqlite".format(thread_id)
    DB_TX_BL_PATH = "../../db/new_tx_block.sqlite"

    pool_size = int((MIX + 1) * 1.5 + 1)
    pool_size = MIX
    # to simplify

    cur_tx_in_out = sqlite3.connect(DB_TX_IN_OUT_PATH).cursor()
    cur_tx_block = sqlite3.connect(DB_TX_BL_PATH).cursor()

    guess_times = [0 for i in range(MIX + 2)]

    k = 0
    while k < SIMU_TIMES:
        if k % 10 == 0:
            disp_progress(t1, 0, k, SIMU_TIMES, str(k))

        selected_mini = [0 for jj in range(pool_size + 1)]

        now_tx = real_tx = real_nfrom = 0
        try:
            while now_tx == 0:
                now_tx, real_tx, real_nfrom = line_txto_txfrom_nfrom(
                    cur_tx_in_out, random.randint(5, SIZE_DB[thread_id] - 1))

            real_block, real_mini_id = block_minitxid_via_txid(
                cur_tx_block, real_tx, real_nfrom)
            now_block, now_mini_id = block_minitxid_via_txid(
                cur_tx_block, now_tx, 0)
            # print("BLOCK at", now_block)

            real_time_ago = get_time_stamp(
                now_block, now_mini_id) - get_time_stamp(real_block, real_mini_id)
            # print("TH", thread_id, "Random Choose:", now_tx, "from",
            #      real_tx, real_nfrom, "mini_id", real_mini_id, "age:",
            #      real_time_ago)
            # row_prob[0] = 1

            selected_mini[0] = real_time_ago

            for j in range(pool_size):
                time_ago = 0
                while time_ago <= 0 or time_ago in selected_mini[0:j + 1]:
                    time_ago = int(math.exp(random.gammavariate(ALPHA, BETA)))
                    #print("ready choose", time_ago)
                    selected_mini[j + 1] = time_ago
            # print("\tTH", thread_id, "choose_time_ago:", selected_mini)

            selected_mini.sort(reverse=True)
            guess_time = find_index(selected_mini, real_time_ago, MIX)
            guess_times[MIX + 1 - guess_time] += 1
            # print("\tTH", thread_id, "final:", now_tx, "from", real_tx,
            #      real_nfrom, "guess time:", MIX + 1 - guess_time)
            k += 1
        except:
            pass

    info = "OK: {}".format(str(guess_times))
    return info

'''
def is_in_array(arr, element, start, end):
    for i in ranage(start, end + 1):
        if arr[i] == element:
            return true
    return false
'''


def find_index(arr, element, largest):
    for i in range(largest, -1, -1):
        if arr[i] == element:
            return i
    print("-1")
    return -1


def timestamp2string(timeStamp):
    try:
        d = datetime.datetime.fromtimestamp(timeStamp)
        str1 = d.strftime("%Y-%m-%d-%H-%M-%S.%f")
        # 2015-08-28 16:43:37.283000'
        return str1
    except Exception as e:
        print(e)
        return ''

if __name__ == '__main__':
    main()
