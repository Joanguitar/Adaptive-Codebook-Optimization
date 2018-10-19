

class MCS_PARSER(object):

    def __init__(self):
        self.cid = 0

        # enable or disable rate search
        self.rs_enable = 0x01

        # The maximal allowed PER for each MCS
        # MCS will be considered as failed if PER during RS is higher
        self.per_threshold = [00, 00, 40, 15, 10, 00, 20, 15, 10, 00, 15, 10, 10]

        # Number of MPDUs for each MCS
        # this is the minimal statistic required to make an educated decision
        self.min_frame_cnt = [0, 32, 64, 64, 64, 0, 80, 80, 80, 00, 160, 160, 160]

        # stop threshold [0-100]
        self.stop_th = 0x01

        # MCS1 stop threshold [0-100]
        self.mcs1_fail_th = 0x50

        self.max_back_failure_th = 0x03

        # Debug feature for disabling internal RS trigger (which is
        # currently triggered by BF Done
        self.dbg_disable_internal_trigger = 0x00

        self.back_failure_mask = [0x10, 0x00]
        self.mcs_on=[False]+[True]*4+[False]+[True]*3+[False]+[True]*3
#        self.mcs_en_vec = [0xde, 0x1d]
    
    def Parse(self):
        parse_str='\\x%02x'
        command_str=''.join([parse_str%a for a in [0, 0, 33, 9, 0, 0, 0, 0]])
        cid_str=parse_str%self.cid
        rx_enable_str=parse_str%self.rs_enable
        per_threshold_str=''.join([parse_str%a for a in self.per_threshold])
        min_frame_cnt_str=''.join([parse_str%a for a in self.min_frame_cnt])
        pretail_str=''.join([parse_str%a for a in [self.stop_th, self.mcs1_fail_th, self.max_back_failure_th, self.dbg_disable_internal_trigger]])
#        pretail_str=''.join([parse_str%a for a in [self.stop_th, self.mcs1_fail_th, self.max_back_failure_th]])
        back_failure_str=''.join([parse_str%a for a in self.back_failure_mask])
        mcs_en_vec=[0]*2
        for ii in range(len(self.mcs_on)-1, 7, -1):
            mcs_en_vec[1]=(mcs_en_vec[1]<<1)+self.mcs_on[ii]
        for ii in range(7, -1, -1):
            mcs_en_vec[0]=(mcs_en_vec[0]<<1)+self.mcs_on[ii]
        mcs_en_vec_str=''.join([parse_str%a for a in mcs_en_vec])
        middle_str=''.join([parse_str%a for a in [0, 0]])
        full_str='%s%s%s%s%s%s%s%s%s%s'%(command_str, cid_str, rx_enable_str, per_threshold_str, min_frame_cnt_str, pretail_str, back_failure_str, middle_str, mcs_en_vec_str, middle_str)
        return '\'%s\''%full_str
    
    def Parsed_CMD(self):
        return 'echo -n -e %s > /sys/kernel/debug/ieee80211/$(ls /sys/kernel/debug/ieee80211/ | tail -n1)/wil6210/wmi_send'%self.Parse()