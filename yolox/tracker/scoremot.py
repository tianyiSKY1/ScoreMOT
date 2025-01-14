import cv2
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
from yolox.tracker import matching_ty as matching
from .basetrack import BaseTrack, TrackState
from .kalman_filter import KalmanFilter
from .kalman_filter_score import KalmanFilter_score



class STrack(BaseTrack):
    shared_kalman = KalmanFilter()
    shared_kalman_score = KalmanFilter_score()
    def __init__(self, tlwh, score):

        # wait activate
        self._tlwh = np.asarray(tlwh, dtype=np.float)
        self.kalman_filter = None
        self.kalman_filter_score = None
        self.mean, self.covariance = None, None
        self.mean_score, self.covariance_score = None, None
        self.is_activated = False

        self.pre_score = score
        self.score = score
        self.tracklet_len = 0

        self.alpha = 0.9


    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[6] = 0
            mean_state[7] = 0

        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][6] = 0
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

            multi_mean_score = np.asarray([st.mean_score.copy() for st in stracks])
            multi_covariance_score = np.asarray([st.covariance_score for st in stracks])
            multi_mean_score, multi_covariance_score = STrack.shared_kalman_score.multi_predict(multi_mean_score, multi_covariance_score)
            for i, (mean_score, cov_score) in enumerate(zip(multi_mean_score, multi_covariance_score)):
                stracks[i].mean_score = mean_score
                stracks[i].covariance_score = cov_score


    def activate(self, kalman_filter, frame_id, kalman_filter_score):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.kalman_filter_score = kalman_filter_score
        self.track_id = self.next_id()
        # self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xywh(self._tlwh))
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyws(self._tlwh))
        self.mean_score, self.covariance_score = self.kalman_filter_score.initiate(self.score)

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):

        # self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_track.tlwh))
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyws(new_track.tlwh))
        self.mean_score, self.covariance_score = self.kalman_filter_score.update(self.mean_score, self.covariance_score, self.score)

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.pre_score = self.score

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1

        new_tlwh = new_track.tlwh

        # self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_tlwh))
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyws(new_tlwh))
        self.mean_score, self.covariance_score = self.kalman_filter_score.update(self.mean_score, self.covariance_score, self.score)

        self.state = TrackState.Tracked
        self.is_activated = True
        self.pre_score = self.score
        self.score = new_track.score



    @property
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        # ret[2] *= ret[3]
        ret[3] /= ret[2]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def score_kalman(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean_score is None:
            return self.score.copy()
        ret = self.mean_score[0].copy()
        return ret

    @property
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    def xywh(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2.0
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlwh_to_xywh(tlwh):
        """Convert bounding box to format `(center x, center y, width,
        height)`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        return ret

    def to_xywh(self):
        return self.tlwh_to_xywh(self.tlwh)

    @staticmethod
    def tlwh_to_xyws(tlwh):

        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[3] *= ret[2]
        return ret

    def to_xyws(self):
        return self.tlwh_to_xyws(self.tlwh)

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)


class ScoreMOT(object):
    def __init__(self, args, frame_rate=30):

        self.tracked_stracks = []  # type: list[STrack]
        self.lost_stracks = []  # type: list[STrack]
        self.removed_stracks = []  # type: list[STrack]
        BaseTrack.clear_count()

        self.frame_id = 0
        self.args = args

        self.track_high_thresh = args.track_high_thresh
        self.track_low_thresh = args.track_low_thresh
        self.new_track_thresh = args.new_track_thresh

        self.buffer_size = int(frame_rate / 30.0 * args.track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()
        self.kalman_filter_score = KalmanFilter_score()



    def update(self, output_results, img):
        self.frame_id += 1
        activated_starcks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []

        if len(output_results):
            if output_results.shape[1] == 5:
                scores = output_results[:, 4]
                bboxes = output_results[:, :4]
                classes = output_results[:, -1]
            else:
                scores = output_results[:, 4] * output_results[:, 5]
                bboxes = output_results[:, :4]  # x1y1x2y2
                classes = output_results[:, -1]

            # Remove bad detections
            lowest_inds = scores > self.track_low_thresh
            bboxes = bboxes[lowest_inds]
            scores = scores[lowest_inds]
            classes = classes[lowest_inds]

            # Find high threshold detections
            remain_inds = scores > self.args.track_high_thresh
            dets = bboxes[remain_inds]
            scores_keep = scores[remain_inds]
            classes_keep = classes[remain_inds]

        else:
            bboxes = []
            scores = []
            classes = []
            dets = []
            scores_keep = []
            classes_keep = []

        if len(dets) > 0:
            '''Detections'''
            detections = [STrack(STrack.tlbr_to_tlwh(tlbr), s) for(tlbr, s) in zip(dets, scores_keep)]
        else:
            detections = []

        ''' Add newly detected tracklets to tracked_stracks'''
        unconfirmed = []
        tracked_stracks = []  # type: list[STrack]
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        ''' Step 2: First association, with high score detection boxes'''
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)

        # Predict the current location with KF
        STrack.multi_predict(strack_pool)

        HighScoreStracks = []
        LowScoreStracks = []
        for track in strack_pool:
            if track.score > 0.8 :
                HighScoreStracks.append(track)
            else:
                LowScoreStracks.append(track)
        '''associate with high score stracks'''
        ious_dists_H = matching.iou_distance(HighScoreStracks, detections)
        # ious_dists_mask_H = (ious_dists_H > self.proximity_thresh)

        # Hstrack_score = np.array([strack.score_kalman for strack in HighScoreStracks])
        # Hstrack_score = np.array([np.clip(strack.score_kalman, 0.6, 1.0) for strack in HighScoreStracks])
        # det_score = np.array([det.score for det in detections])
        # ious_dists_H += (abs(np.expand_dims(Hstrack_score, axis=1).repeat(ious_dists_H.shape[1],axis=1) - det_score) * 1.0)
        # matches_H, u_track, u_detection = matching.linear_assignment(dists_H, thresh=self.args.match_thresh)
        matches_H, u_track, u_detection = matching.linear_assignment(ious_dists_H, thresh=0.8)
        for itracked, idet in matches_H:
            track = HighScoreStracks[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        detections = [detections[i] for i in u_detection]
        r_tracked_stracks_low = [HighScoreStracks[i] for i in u_track if HighScoreStracks[i].state == TrackState.Tracked]
        LowScoreStracks = joint_stracks(LowScoreStracks, r_tracked_stracks_low)
        ''' Step 3: Second association, with low score detection boxes'''
        '''associate with low score stracks'''
        ious_dists_L = matching.iou_distance(LowScoreStracks, detections)
        # ious_dists_mask_L = (ious_dists_L > self.proximity_thresh)

        # Lstrack_score = np.array([strack.score_kalman for strack in LowScoreStracks])

        # Lstrack_score = np.array([np.clip(strack.score_kalman, 0.3, 0.8) for strack in LowScoreStracks]) // dance
        Lstrack_score = np.array([np.clip(strack.score_kalman, 0.3, 0.8) for strack in LowScoreStracks])
        det_score = np.array([det.score for det in detections])
        ious_dists_L += (abs(np.expand_dims(Lstrack_score, axis=1).repeat(ious_dists_L.shape[1], axis=1) - det_score) * 1.0)

        # matches_L, u_track, u_detection = matching.linear_assignment(dists_L, thresh=self.args.match_thresh)
        matches_L, u_track, u_detection = matching.linear_assignment(ious_dists_L, thresh=0.8)
        for itracked, idet in matches_L:
            track = LowScoreStracks[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        ''' Step 3: Third association, with low score detection boxes'''


        if len(scores):
            inds_high = scores < self.args.track_high_thresh
            inds_low = scores > self.args.track_low_thresh
            inds_second = np.logical_and(inds_low, inds_high)
            dets_second = bboxes[inds_second]
            scores_second = scores[inds_second]
            classes_second = classes[inds_second]
        else:
            dets_second = []
            scores_second = []
            classes_second = []



        # association the untrack to the low score detections
        if len(dets_second) > 0:
            '''Detections'''
            detections_second = [STrack(STrack.tlbr_to_tlwh(tlbr), s) for
                                 (tlbr, s) in zip(dets_second, scores_second)]

        else:
            detections_second = []

        r_tracked_stracks = [LowScoreStracks[i] for i in u_track if LowScoreStracks[i].state == TrackState.Tracked]

        dists = matching.iou_distance(r_tracked_stracks, detections_second)
        # r_strack_score = np.array([np.clip(strack.score_kalman, 0.1, 0.6) for strack in r_tracked_stracks])
        # det_score = np.array([det.score for det in detections_second])
        # dists += (abs(np.expand_dims(r_strack_score, axis=1).repeat(dists.shape[1], axis=1) - det_score) * 1.0)

        # matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.7)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        for it in u_track:
            track = r_tracked_stracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)

        '''Deal with unconfirmed tracks, usually tracks with only one beginning frame'''
        detections = [detections[i] for i in u_detection]
        ious_dists = matching.iou_distance(unconfirmed, detections)
        if not self.args.mot20:
            ious_dists = matching.fuse_score(ious_dists, detections)

        dists = ious_dists

        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_starcks.append(unconfirmed[itracked])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)

        """ Step 4: Init new stracks"""
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.new_track_thresh:
                continue

            track.activate(self.kalman_filter, self.frame_id, self.kalman_filter_score)
            activated_starcks.append(track)

        """ Step 5: Update state"""
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)

        """ Merge """
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)

        # output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        output_stracks = [track for track in self.tracked_stracks]


        return output_stracks


def joint_stracks(tlista, tlistb):
    exists = {}
    res = []
    for t in tlista:
        exists[t.track_id] = 1
        res.append(t)
    for t in tlistb:
        tid = t.track_id
        if not exists.get(tid, 0):
            exists[tid] = 1
            res.append(t)
    return res


def sub_stracks(tlista, tlistb):
    stracks = {}
    for t in tlista:
        stracks[t.track_id] = t
    for t in tlistb:
        tid = t.track_id
        if stracks.get(tid, 0):
            del stracks[tid]
    return list(stracks.values())


def remove_duplicate_stracks(stracksa, stracksb):
    pdist = matching.iou_distance(stracksa, stracksb)
    pairs = np.where(pdist < 0.15)
    dupa, dupb = list(), list()
    for p, q in zip(*pairs):
        timep = stracksa[p].frame_id - stracksa[p].start_frame
        timeq = stracksb[q].frame_id - stracksb[q].start_frame
        if timep > timeq:
            dupb.append(q)
        else:
            dupa.append(p)
    resa = [t for i, t in enumerate(stracksa) if not i in dupa]
    resb = [t for i, t in enumerate(stracksb) if not i in dupb]
    return resa, resb
