from eastwood import AlpacaAccount, PairsTrader
from eastwood import PairsTrader
import yaml
from datetime import time, datetime, timedelta

auth = yaml.load(open('eastwood/paper_key.yml','r'), Loader=yaml.CLoader)
acct = AlpacaAccount(**auth)
t = time(19, 0)
data_start = datetime.today() - timedelta(days=365*3)
pairs = [('MCD','WEN'),('APA', 'COP'),('SLB', 'EQT'),('MPC', 'WMB'),('OKE', 'PSX'),('ENB', 'BKR'),('NOG', 'VLO')]

pt = PairsTrader(acct, pairs=pairs, trade_time=t, start=data_start, tolerance=1.0)

print(pt.acct.get_price('AAPL'))
from time import sleep
sleep(5)
print(pt.acct.get_price('AAPL'))

print("Now we're implementing the strategy!")
pt.run()