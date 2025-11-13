CROP_IGNORED_PARAMS = {
    'dummy - Parameter no Longer required',
    'Dummy - no longer applicable',
}

CROP_FIELD_NDIGITS = {
   'Shape factor for water stress coefficient for canopy expansion (0.0 = straight line)': 1,
   'Shape factor for water stress coefficient for stomatal control (0.0 = straight line)': 1,
   'Shape factor for water stress coefficient for canopy senescence (0.0 = straight line)': 1,
   'Vol% for Anaerobiotic point (* (SAT - [vol%]) at which deficient aeration occurs *)': 0,
   'Canopy growth coefficient (CGC): Increase in canopy cover (fraction soil cover per day)': 5,
   'Canopy decline coefficient (CDC): Decrease in canopy cover (in fraction per day)': 5,
   'Reference Harvest Index (HIo) (%)': 0,
}

DAILY_OUT_WIDTHS = (
   6, 12, 18, 24, 30, 40, 48, 57, 64, 71, 78, 87, 96, 104, 113, 122, 129, 138, 147, 153, 162, 170,
   178, 187, 195, 202, 209, 216, 223, 230, 238, 246, 253, 262, 271, 280, 289, 295, 303, 313, 321,
   330, 339, 347, 359, 368, 377, 387, 396, 404, 412, 422, 432, 442, 452, 462, 472, 481, 491, 501,
   511, 521, 529, 538, 546, 553, 561, 569, 580, 591, 602, 613, 624, 635, 646, 657, 668, 679, 690,
   701, 712, 723, 734, 745, 756, 767, 778, 789, 800, 811, 822, 833, 842, 852, 862, 872, 882, 892,
)

DAILY_OUT_HEADER = (
   'Date', 'DAP', 'Stage', 'WC(****)', 'Rain', 'Irri', 'Surf', 'Infilt', 'RO', 'Drain', 'CR',
   'Zgwt', 'Ex', 'E', 'E/Ex', 'Trx', 'Tr', 'Tr/Trx', 'ETx', 'ET', 'ET/ETx', 'GD', 'Z', 'StExp',
   'StSto', 'StSen', 'StSalt', 'StWeed', 'CC', 'CCw', 'StTr', 'Kc(Tr)', 'Trx', 'Tr', 'TrW',
   'Tr/Trx', 'WP', 'Biomass', 'HI', 'Y(dry)', 'Y(fresh)', 'Brelative', 'WPet', 'Bin', 'Bout',
   'WC(****)', 'Wr(****)', 'Z', 'Wr', 'Wr(SAT)', 'Wr(FC)', 'Wr(exp)', 'Wr(sto)', 'Wr(sen)',
   'Wr(PWP)', 'SaltIn', 'SaltOut', 'SaltUp', 'Salt(****)', 'SaltZ', 'Z', 'ECe', 'ECsw', 'StSalt',
   'Zgwt', 'ECgw', 'WC01', 'WC 2', 'WC 3', 'WC 4', 'WC 5', 'WC 6', 'WC 7', 'WC 8', 'WC 9', 'WC10',
   'WC11', 'WC12', 'ECe01', 'ECe 2', 'ECe 3', 'ECe 4', 'ECe 5', 'ECe 6', 'ECe 7', 'ECe 8', 'ECe 9',
   'ECe10', 'ECe11', 'ECe12', 'Rain', 'ETo', 'Tmin', 'Tavg', 'Tmax', 'CO2',
)
