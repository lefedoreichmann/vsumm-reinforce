import numpy as np
from knapsack import knapsack_dp
import math

def generate_summary(ypred, cps, n_frames, nfps, positions, proportion=0.15):
    """ Generate keyshot-based video summary i.e. a binary vector
    ypred: predicted importance scores.
    cps: change points, 2D matrix, each row contains a segment.
    n_frames: original number of frames.
    nfps: number of frames per segment.
    positions: positions of subsampled frames in the original video.
    proportion: length of video summary (compared to original video length).
    """
    n_segs = cps.shape[0]
    frame_scores = np.zeros((n_frames), dtype=np.float32)
    if positions.dtype != int:
        positions = positions.astype(np.int32)
    if positions[-1] != n_frames:
        positions = np.concatenate([positions, [n_frames]])
    for i in range(len(positions) - 1):
        pos_left,pos_right = positions[i],positions[i+1]
        frame_scores[pos_left:pos_right] = ypred[i]

    seg_score = []
    for seg_idx in range(n_segs):
        start,end = int(cps[seg_idx,0]),int(cps[seg_idx,1]+1)
        scores = frame_scores[start:end]
        seg_score.append(float(scores.mean()))

    limits = int(math.floor(n_frames * proportion))
    picks = knapsack_dp(seg_score, nfps, n_segs, limits)

    summary = np.zeros((1), dtype=np.float32) # this element should be deleted
    for seg_idx in range(n_segs):
        nf = nfps[seg_idx]
        if seg_idx in picks:
            tmp = np.ones((nf), dtype=np.float32)
        else:
            tmp = np.zeros((nf), dtype=np.float32)
        summary = np.concatenate((summary, tmp))

    summary = np.delete(summary, 0) # delete the first element
    return summary

def evaluate_summary(machine_summary, user_summary, eval_metric='avg'):
    """ Compare machine summary with user summary (keyshot-based).
    machine_summary and user_summary should be binary vectors of ndarray type.
    eval_metric = {'avg', 'max'} """
    machine_summary = machine_summary.astype(np.float32)
    user_summary = user_summary.astype(np.float32)
    n_users,n_frames = user_summary.shape

    # binarization
    machine_summary[machine_summary > 0] = 1
    user_summary[user_summary > 0] = 1

    if len(machine_summary) > n_frames:
        machine_summary = machine_summary[:n_frames]
    elif len(machine_summary) < n_frames:
        zero_padding = np.zeros((n_frames - len(machine_summary)))
        machine_summary = np.concatenate([machine_summary, zero_padding])

    f_scores = []
    prec_arr = []
    rec_arr = []

    for user_idx in range(n_users):
        gt_summary = user_summary[user_idx,:]
        overlap_duration = (machine_summary * gt_summary).sum()
        precision = overlap_duration / (machine_summary.sum() + 1e-8)
        recall = overlap_duration / (gt_summary.sum() + 1e-8)
        if precision == 0 and recall == 0:
            f_score = 0.
        else:
            f_score = (2 * precision * recall) / (precision + recall)
        f_scores.append(f_score)
        prec_arr.append(precision)
        rec_arr.append(recall)

    if eval_metric == 'avg':
        final_f_score = np.mean(f_scores)
        final_prec = np.mean(prec_arr)
        final_rec = np.mean(rec_arr)
    elif eval_metric == 'max':
        final_f_score = np.max(f_scores)
        max_idx = np.argmax(f_scores)
        final_prec = prec_arr[max_idx]
        final_rec = rec_arr[max_idx]

    return final_f_score,final_prec,final_rec

if __name__ == '__main__':
    pass
