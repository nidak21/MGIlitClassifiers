Using machine learning to automate literature triage tasks.

Backpopulate/  
    - code for getting old articles that curators have not selected in the past.
	These are negative, non-MGI-relevant articles.

Lessons Learned and Where We Are

Understanding Vectorizers
    vect = CountVectorizer( stop_words="english", ngram_range=(1,2))
    * tokenized 1st (e.g., break/remove punct), stopwords are removed,
	then ngrams built, then min_df/max_df applied

Dec 5 2018: vectorizer things:
    in extracted text:
	** *** and **** can appear as tokens aa aaa and aaaa
	+/- can appear as "ae"
	might want to remove doi:... in addition to URLs
	"knock in" and "knock down" are fairly common ("knock" in 5.3% docs)


Previous thinking for python scripts in MLtextTools:
    * getTrainingData.py would get a delimited file of samples
    * preprocessSamples.py would massage the data in the delimited file(s)
    * populateTrainigDirs.py would take a massaged delimited file and populate
	the dirs that sklearn's load_files() wants.
    Would it be better to have getTrainingData populate text files in the dirs
    and massage the data in place (or into additional cooked files)?

    BUT MLtextTools already has stuff in place, so lets keep with that 
    paradigm. Can always run populateTrainingDirs.py at any time to generate
    the text files to look at.
    	- should add parameter to specify file extension (done)
	- should make it not assume class names are 'yes' 'no' (done)

NER thoughts
    Becas is very unreliable, down much of the time.
    Haven't found any other online tool (need to look some more).
    Pubtator does NER on pubmed abstracts and titles, but it won't do anything
	with figure text.
    I'm pondering doing some simple, easy to code, dictionary lookup approach
    myself.
	It doesn't have to be perfect, or even very good maybe.
	But where to get the dictionary? Some thoughts:
	    Build by hand from MGI gene symbols and ontology terms?
	    Pull mapping files for all of pubmed from Pubtator and distill
		out the entity mappings - easy to program, but a honking pile
		of data.
	    For our particular set of pubmed IDs, pull the mappings out of 
		Pubtator and apply those mappings to the figure text?
		(would be a much smaller set of mappings and likely more
		relevant/specific to our references??)

		I'm kind of liking this idea.
		(unfortunately, Pubtator doesn't do anatomy)

    I guess the first thing is to get an initial training pipeline built
	without NER.
...
Dear Diary:

Dec 5, 2018
    Grabbed dataset to use going forward (for now)

    Idea: should write a script to calculate recall foreach curation group.
	Note, cannot really do precision since all the papers for each
	curation group are already "Keep" (so there are no false positives)

Dec 6, 2018
    Cannot do ngrams (1,3) - blows out the memory on my Mac

    Tried not removing stopwords and using feature counts instead of binary,
    these do not seem to be helpful at this point...

    Analyzed F-scores in https://docs.google.com/spreadsheets/d/1UpMNN4Qj1Ty9pYiQ4ZBspq2fef2qTeybHZMDc35Que8/edit#gid=1787124464

    Decided best for reporting "success" is F2 with values > 0.85.

    Still using F4 during gridsearch to weigh results toward recall, but
    this is questionable.

Dec 7, 2018
    using Dec5/Proc1
    Seemingly good, out of the box pipeline:  2018/12/07-09-21-48  SGDlog.py
    alpha = 1
    min_df = .02
    ngrams = (1,2)
    stopwords = english
    binary
    Gets (test) Precision: .61, Recall: .91, F2: .83

    Looking at false negative 28228254
	some Fig legends are split across page boundaries (so only get 1st part).
	Supplemental figures won't be found because they start with "Supplemental
	Figure" instead of just "Figure".
	"mice" only occurs in figure legend text skipped because of the above
	reasons & not in title/abstract

	Maybe we should omit "mice" as a feature since these are all supposed to
	be mice papers anyway ??

	Need to look at more FP FN examples examples examples examples
    false neg 27062441
	indexed by pm2gene, not selected for anything else. Monica says she
	would not select it a relevant since it is about human protein. 
	So this is really a true negative.
	Maybe we want to remove these from the whole raw set?

    Text transformations
	Looking at Jackie's 1-cell, one-cell, ... these seem relevant.
	should add these
    Changes
	* figureText.py - to include figure paragraphs that begin "supplemental
	    fig"
	* omit doi Ids along with URLs

Dec 8, 2018
    using Dec5/Proc2

    added more feature transformations
	1-cell ...
	knock in (in addition to knock-out)
	gene trap

    gets us to precision 60, recall 92

    Need to look at Debbie's "oma" transformations.
	In the current set of features, there is only one feature: carcinoma
	- but maybe if we collapse the other oma's, this feature would boosted.
	But have to factor out glaucoma. Are there others?
	Need to investigate.
Dec 10, 2018
    Added all the MTB "oma"s to feature transformation --> "tumor_type"

    On classifier prior to these additional feature transforms, investigating
    some FN
	27062441 - predicted discard, IS actually discard - discarded after I
			grabbed the data set
	26676765 - only pm2gene - probably not relevant - check
	26094765 - only pm2gene
	12115612 - text extracted ok. Need curator to review
    looking at some FP
	28538185 - Cell Reports - fig 3 legend text lost due to funky splitting
	    across pages, but other figures intact. Need curator to reviewj
	28052251 - Cell Reports - fig 2 partially lost due to split
	28614716 - Cell Reports - fig 1,3 partially lost due to split
	28575432 - Endocrinology - just a "news and reviews" very short
	28935574 - lots of fig text missing: 1,2,4,5,7,12,13 - seems trouble
	    finding beginning of fig text (only finding "Figure x"

    On classifier with new tumor_type transformation: no improvement of
	precision and recall: 61 and 92
	interestingly "tumor_typ" is a highly negative term (???)

Dec 11, 2018 SGDlog
    I want to see how well the relevance automation works for papers
    selected by the different groups.

    Wrote tdataDocStatus.py to pull article curation statuses out of the db.
    Wrote tdataGroupRecall.py to use those statuses + a prediction file compute
	the recall for papers selected for each curation group.

    based on current predictions for the current test set:
    Recall for papers selected by each curation group
    ap_status      selected papers:  1658 predicted keep:  1584 recall: 0.955
    gxd_status     selected papers:   167 predicted keep:   166 recall: 0.994
    go_status      selected papers:  1910 predicted keep:  1796 recall: 0.940
    tumor_status   selected papers:   178 predicted keep:   132 recall: 0.742
    qtl_status     selected papers:     7 predicted keep:     5 recall: 0.714
    Totals         selected papers:  2268 predicted keep:  2082 recall: 0.918

    The smaller number of papers for tumor and GXD match the smaller number
    of papers actually chosen/indexed/full-coded in the database since
    Oct 2017.  Roughly 10% of A&P and GO.

    Makes me think we need to look at the distributions in the test/validation
    sets from two axes (at least):
	by journal - and really should be by keep/discard by journal
	by curation group selection
    and make sure they match the distributions of all the data since Oct 2017.
    (it looks like they do for curation group selection)

Dec 12, 2018 SGDlog
    Looking at papers indexed for GO by pm2geneload that have not been deemed
    relevant by any curator...
	select distinct a.accid pubmed
	from bib_refs r join bib_workflow_status bs on
			    (r._refs_key = bs._refs_key and bs.iscurrent=1 )
	join bib_status_view bsv on (r._refs_key = bsv._refs_key)
	     join acc_accession a on
		 (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
		  and a._mgitype_key=1 )
	where 
	(bs._status_key = 31576673 and bs._group_key = 31576666 and 
	    bs._createdby_key = 1571) -- index for GO by pm2geneload
	and bsv.ap_status in ('Not Routed', 'Rejected')
	and bsv.gxd_status in ('Not Routed', 'Rejected')
	and bsv.tumor_status in ('Not Routed', 'Rejected')

    Finds 1758 papers. Seems like these should be removed from the sample set
    because we don't know for sure that these are really MGI relevant.
    (1758 is about 3.5% of our sample papers)

dec 19, 2018 SGDlog
    Changed tdataGetRaw.py to skip the pm2gene references as above.
    Used that to grab updated date in Data/dec19.

    Retraining/evaluating get tiny improvement:
    2018/12/19-12-46-56     PRF2,F1 0.62    0.92    0.84    0.74    SGDlog.py

    Recall for papers selected by each curation group (FOR TEST SET PREDS)
    ap_status      selected papers:  1664 predicted keep:  1592 recall: 0.957
    gxd_status     selected papers:   163 predicted keep:   160 recall: 0.982
    go_status      selected papers:  1789 predicted keep:  1696 recall: 0.948
    tumor_status   selected papers:   187 predicted keep:   142 recall: 0.759
    qtl_status     selected papers:     4 predicted keep:     4 recall: 1.000
    Totals         selected papers:  2153 predicted keep:  1989 recall: 0.924

    Added initial set of cell line transformations - those that are cell line
    prefixes. No improvement.

    Realized I'd like to see what these group recall numbers look like for
    the training and validation sets. To get these, need a longer time frame
    of paper statuss. Need to update tdataGetStatus.py for earlier date range

Dec 20, 2018 SGDlog
    changed tdataGetStatus.py as above. Interesting, a little worse:
    Recall for papers selected by each curation group (FOR TRAINING SET PREDS)
    ap_status      selected papers: 17877 predicted keep: 16976 recall: 0.950
    gxd_status     selected papers:  2019 predicted keep:  1993 recall: 0.987
    go_status      selected papers: 16491 predicted keep: 15365 recall: 0.932
    tumor_status   selected papers:  1735 predicted keep:  1286 recall: 0.741
    qtl_status     selected papers:   137 predicted keep:    74 recall: 0.540
    Totals         selected papers: 21544 predicted keep: 19602 recall: 0.910

    No idea what that means!

    wrote wrapper scripts for extracting fig text and preprocessing the train,
    test, & val data files

    added cell line names (not prefixes) to transformations. No change really.

    Looking at tumor papers/stats. Why is tumor recall so low? The counts of
    papers and papers by status are very close to gxd papers.
    So it doesn't seem that the training/test sets would somehow be skewed to
    not include enough tumor papers (???). 
    However it does seem that tumor papers are harder to recognize (hence more
    false negatives).

Dec 21, 2018 SGDlog
    Updated tdataGroupRecall.py to optionally output rows that combine a
    paper's prediction with it curation statuses.
    So you can look at tumor FN or AP FN, etc.
    Not sure how much it helps.
    BUT the vast majority of tumor FN  (41 of 45) are not selected for any
    other group and the vast majority of TP are selected by other group.
    I guess this just clarifies, tumor papers are harder to
    detect. If they are relevant to any other group, they are easier to detect.
    This seems less true for GXD AP FN (just by eyeball).:w
    
    Talked with Debbie about Tumor recall. She says tumor is the only group
    that still "chooses" review papers. So there are possibly tumor selected
    review papers that are not being recognized by the classifier.
    I will work on removing review papers from the sample set and see what
    happens.

Dec 27, 2018 SGDlog
    Lots of file renaming for sanity sake.
    
Jan 2, 2019 SGDlog
    Refactored sdGetRaw.py to break out SQL parts to simply queries and support
    getting sample record counts.
    Counts of samples OMITTING review articles
    Wed Jan  2 14:37:28 2019
       1407	Omitted references (only pm2gene indexed)
      27439	Discard since 11/1/2017
      18709	Keep since 11/1/2017
       7793	Keep 10/01/2016 through 10/31/2017

    Counts of samples INCLUDING review articles
    Wed Jan  2 14:38:21 2019
       1407	Omitted references (only pm2gene indexed)
      29235	Discard since 11/1/2017
      18914	Keep since 11/1/2017
       7839	Keep 10/01/2016 through 10/31/2017

    So there are ~2000 review articles that are discards,
    and ~200 that are keep
    Omitting these helps overall P/R and tumor R some.
	Without review articles: (compare to Dec 20 above)
    Recall for papers selected by each curation group
    ap_status      selected papers:  1710 predicted keep:  1634 recall: 0.956
    gxd_status     selected papers:   183 predicted keep:   182 recall: 0.995
    go_status      selected papers:  1755 predicted keep:  1661 recall: 0.946
    tumor_status   selected papers:   147 predicted keep:   115 recall: 0.782
    qtl_status     selected papers:     3 predicted keep:     1 recall: 0.333
    Totals         selected papers:  2127 predicted keep:  1970 recall: 0.926
	Here is overall P/R for Dec 20 (w/ review papers) vs. Jan 2 (without)
    2018/12/20-13-46-18     PRF2,F1 0.63    0.92    0.84    0.75    SGDlog.py
    2019/01/02-16-08-32     PRF2,F1 0.65    0.93    0.85    0.76    SGDlog.py

Jan 3, 2019 SGDlog
    Realized that I CAN compute a precision value for individual curation
    groups. I can get papers that are "negative" for a given group by counting
    "discard" papers and papers that are rejected by the group. These should
    be ground truth negatives for the group.

    I'll convert groupRecall.py to output both, and output sets of FN and FP
    for each group so we can easily look at examples for each group that
    are wrongly predicted. (will rename the script too!)

    Hmmm. need to think about this more, I thought it made sense, but now I'm
    not so sure. (SEE JAN 4)

Jan 4, 2019 SGDlog
    Group Recall question:
	How many relevant papers will my group miss? (neg stmt)
	Really: what fraction of papers predicted "discard" should be selected
	    by my group? (neg stmt)
	Really: what fraction of group selected papers will be predicted "keep"
	    (i.e., will we look at) (pos stmt)
	To answer:
	    GRecall = group selected predicted keep / group selected

	    In terms of TP and TN:
	    GTP = predicted_keep(restricted to group selected)
	    		# (group selected => ground truth pos)
	    GFN = predicted_discard(restricted to group selected)
	    GTP + GFN = group selected
	    GRecall = GTP/(GTP + GFN) = GTP/(group selected)

    Group Precision question:
	How many papers will my group look at that we don't want? (neg stmt)
	Really:  what fraction of papers predicted "keep" will be
	    rrelevant to my group? (neg stmt)
	    (reject or will be skipped by 2nd triage report)
	Really:  what fraction of papers my group looks at will be
	    relevant to my group? (pos stmt)
	    (selected by my group)
	    BUT "what papers my group looks at" also dependes on the group's
		2ndary triage selection report. So if we cannot take that
		into account, I'm not sure how useful this is.
	To answer:
	    GPrecision = group selected predicted keep / predicted keep

	    In terms of TP and TN:
	    GTP as above + predicted_keep(restricted to group selected)
	    GFP = predicted_keep(restricted to not group selected)
		    kind of murky,
		    does "not group selected" = rejected
						or (rejected or true discard)?
		So what does GTP + GFP include?

	    GPrecision = GTP/(GTP + GFP)

	GOING TO PUNT ON THIS FOR NOW.

	Looking at Tumor FN's. Send a small batch to Debbie.
	Looking at a few (general) FP. Send a few to Debbie to look at.

Jan 7-8, 2019 SGDlog
    Debbie and Sue looked at a few tumor FN and general FP examples from the
    most recent SGDlog runs.
    Debbie: of 5 tumor FN examples from the
	29414305 (???mouse??? ???mice??? do not occur in any of the used text fields)
	27760307 (has ???mouse???)
	28430874 (no ???mouse??? ???mice???)
	28647610
	28740119
	all 5 are actually review papers, not marked as review in MGI - 3 ARE
	marked as review in pubmed, 2 not.
	So there are some papers in MGI that have not been marked as review
	when they are in pubmed. These should be found and corrected.
	So for these examples, if we correctly filter out review papers, they
	would not be in the sample set and not be FN
	(additional FN that are reviews: 28412456, 20977690)
    Debbie/Sue looked at 4 FP
	28414311
	25362208
	27317833
	28887218
	the 1st 3 should not have been discarded (they are actually TP)
	the last is a zebrafish paper, so a correct FP
    Sent some more examples, and ones that are not review papers.

    ALSO started looking at randomforest classifier. Promising results, but
    overfitting badly. Looking at ways to stop that.

Jan 9, 2019
    Play w/ n_estimators, max_features, max_samples_split.

    Changed textTuningLib .fit() method to predict on the val set BEFORE
    retraining the bestEstimator on training + val sets.
    This SHOULD make the results on the val set similar to the test set.
    But for RF, the val set is getting similar results as the training set.
    Very weird (this was also happening when I was predicting the val set
    after retraining on training + val).
    I don't understand it.
	- looked at SGDlog.log, it has the expected behavior: val results like
	    test, even when predicting val on the retrained model
	- looked at the way val and test sets were generated to see if they
	    were somehow different, but their journal distributions are very
	    close
    So, there is something weird about RF and the val set.

Jan 10, 2019
    Learned,
    (1) with the gridsearch "refit" parameter, default is to retrain on
    the full train + val sets or train (without removed cv folds).
    So we don't need to retrain.
    (2) if when we predict val set on the trained estimator, it scores like
    the training set, probably is evidence of overfitting - adding the val
    set to train on makes it learn the val set same as rest of the train
    set. If the val set scores like test set (or intermediate), then things
    seem good.

    Restructured textTuningLib gridsearch to not redundantly retrain.

    Finally found params the stop overfitting:
	'classifier__n_estimators': [50],
	'classifier__max_depth': [15],
	'classifier__min_samples_split': [75,],
    Need to try to improve P & R now (R actually)

Jan 14, 2019
    trying various params for RandomForestClassifier.
    See https://docs.google.com/spreadsheets/d/1UpMNN4Qj1Ty9pYiQ4ZBspq2fef2qTeybHZMDc35Que8/edit#gid=1765328280
    Seems playing with Min_samples_leaf is easiest way to control overfitting.
    Seems unnecessary to go beyond 50 estimators.
    Using: 25 (or 5) max_samples_leaf and 50 estimators gives
	P: 83   R: 87  with not too bad overfitting.
	Group recall:
    Recall for papers selected by each curation group
    ap_status      selected papers:  1710 predicted keep:  1553 recall: 0.908
    gxd_status     selected papers:   183 predicted keep:   177 recall: 0.967
    go_status      selected papers:  1755 predicted keep:  1576 recall: 0.898
    tumor_status   selected papers:   147 predicted keep:   115 recall: 0.782
    qtl_status     selected papers:     3 predicted keep:     1 recall: 0.333
    Totals         selected papers:  2127 predicted keep:  1849 recall: 0.869

    I don't see how to get much better w/ random forest - but this is pretty
    good!

Jan 15, 2019
    looking into MGI vs. pubmed review status.
    Started checkRevPaper.py, ran into problems with NCBIutilsLib.py regarding
    getting xml vs. json vs. medline outputs from pubmed.
    Figured out rettype vs. retmode parameters to eutils summary and fetch
    cmds. Subtle confusion.

Jan 16, 2019
    checkRevPaper.py working for comparing "Review" setting in MGI vs. pubmed.
    Found flakeyness @ pubmed. Sometimes data for a pubmed ID will work time,
    later, the same ID gets an error, later it works again...

    initial finding:
    Out of 53938 papers, review in pubmed but not MGI: 2109
    (these are of the sample set which excluded MGI "review" papers)
    Some IDs got kicked out by pubmed.

    Starting to work on detecting review papers by finding "review" in text
    near the beginning of doc.

Jan 18, 2019
    have initial version of text searching for "review". Finding the end of
    the abstract is a bit challenging.
    Taking the last 5 words of the abstract,
    searching for this words upto len(title) + len(abstact) + N words in
    the extracted - I didn't want to convert the whole extracted text into a
    list of words, but maybe I should not worry about that. Or at least make
    N very big.
    Cannot find the end of the abstract for some papers for various reasong:
	1) words/terms are not extracted exactly right, e.g., foo-blah may
	    be extracted as fooblah
	2) N is not big enough - this seems biggest culprit, setting N=2000 
	    removes lots examples.
	3) multiple columns or other weird text flows may not put the abstract
	    text first. Other paragraphs may come 1st
	BUT still out of 1000 papers, we don't find end of abstract about 120
	times
    Ok, code cleaned up, looking at 2000 papers (not marked as review in MGI)
	Papers examined: 2000
	Marked  review in pubmed but not MGI: 106
	Appears review via text but not MGI: 93
	Appears review via text AND in MGI: 0
	Appears review via text AND in pubmed: 59

Jan 25, 2019
    Remembering where I left off. Cleaned up checkRevPaper.py.
    Added basicLib.py to autolittriage.
    Ran checkRevPaper.py on all the raw sample files (discard_after, keep_*).
	Papers examined: 53943
	Marked  review in pubmed but not MGI: 2128
	Appears review via text but not MGI: 3279
	Appears review via text AND in MGI: 0
	Appears review via text AND in pubmed: 1394
    So approx 10% of potential review papers are NOT marked as review in MGI
    (if we believe the text heuristic)

    Put into google spreadsheet:
    https://docs.google.com/spreadsheets/d/1UpMNN4Qj1Ty9pYiQ4ZBspq2fef2qTeybHZMDc35Que8/edit#gid=1956366526

    Spot checking some.
	* some "review found at ..." are matching "received/sent for review"
	    at PNAS. Probably should keep "review" if preceeded by "for"
    
    Need to write a script to remove any review docs from the raw input before
    we do sdSplitByJournal.py.

Jan 28, 2019
    After further clean up of checkRevPaper.py - in particular adding a bunch
    of exceptions where "review" does not mean a review paper,
    (Biochim_Biophys_Acta and PNAS were worst offenders) we get:
	Papers examined: 53943
	Marked  review in pubmed but not MGI: 2128
	Appears review via text but not MGI: 1672
	Appears review via text AND in MGI: 0
	Appears review via text AND in pubmed: 1382
    So this is 2418 additional "review" papers found ~5% of the sample set.
    Could be significant. (maybe?)

    NOTE in 5785 articles, we couldn't find end of abstract, we we did not
    search for "review". So there could be a chunk of review papers here.
    Would have to work harder to see if any could be gleened from this set.

    Wrote rmReviews.py to read in the review predictions file and use it
	to remove review papers from sample data files
    
    Removes ~2400 review papers from full sample set

    Running RF on FULL sample set:
    Recall for papers selected by each curation group
    ap_status      selected papers:  1710 predicted keep:  1553 recall: 0.908
    gxd_status     selected papers:   183 predicted keep:   177 recall: 0.967
    go_status      selected papers:  1755 predicted keep:  1576 recall: 0.898
    tumor_status   selected papers:   147 predicted keep:   115 recall: 0.782
    qtl_status     selected papers:     3 predicted keep:     1 recall: 0.333
    Totals         selected papers:  2127 predicted keep:  1849 recall: 0.869
    2019/01/14-14-07-40     PRF2,F1 0.82    0.87    0.86    0.85    RF.py

    Running RF on review removed sample set:
    Recall for papers selected by each curation group
    ap_status      selected papers:  1635 predicted keep:  1476 recall: 0.903
    gxd_status     selected papers:   183 predicted keep:   170 recall: 0.929
    go_status      selected papers:  1747 predicted keep:  1541 recall: 0.882
    tumor_status   selected papers:   152 predicted keep:   116 recall: 0.763
    qtl_status     selected papers:     3 predicted keep:     2 recall: 0.667
    Totals         selected papers:  2111 predicted keep:  1818 recall: 0.861
    2019/01/28-17-22-41     PRF2,F1 0.83    0.86    0.85    0.84    RF.py

    SO all recalls and other metrics dropped. Doesn't seem to help.
    Might need to retune RF params

Jan 29, 2019
    SGDlog on full sample set (from Dec 19)
    Recall for papers selected by each curation group (FOR TEST SET PREDS)
    ap_status      selected papers:  1664 predicted keep:  1592 recall: 0.957
    gxd_status     selected papers:   163 predicted keep:   160 recall: 0.982
    go_status      selected papers:  1789 predicted keep:  1696 recall: 0.948
    tumor_status   selected papers:   187 predicted keep:   142 recall: 0.759
    qtl_status     selected papers:     4 predicted keep:     4 recall: 1.000
    Totals         selected papers:  2153 predicted keep:  1989 recall: 0.924
    2018/12/19-17-07-12     PRF2,F1 0.63    0.92    0.84    0.75    SGDlog.py

    Running SGDlog on the review removed sample set:
    Recall for papers selected by each curation group
    ap_status      selected papers:  1635 predicted keep:  1546 recall: 0.946
    gxd_status     selected papers:   183 predicted keep:   179 recall: 0.978
    go_status      selected papers:  1747 predicted keep:  1626 recall: 0.931
    tumor_status   selected papers:   152 predicted keep:   120 recall: 0.789
    qtl_status     selected papers:     3 predicted keep:     2 recall: 0.667
    Totals         selected papers:  2111 predicted keep:  1937 recall: 0.918
    2019/01/29-08-48-28     PRF2,F1 0.64    0.92    0.85    0.76    SGDlog.py

    SO slight overall improvement, a little tumor recall improvement, but
    others dropped a tad.

    SO: do I try to improve the review detection code?
    Ideas:
	* (DONE) if we cannot find end of abstract text, just use
	    len(title) + len(abstract) + N as the area to search for "review"
	    words (probably most bang for buck as ~5800 samples don't find
	    eoabstract.
	* (DONE) add "commentary" to list of review words (seems PNAS
	    uses this word).
	    = NEED to EVALUATE THIS MORE
	* after discovering a "review" word exception, keep going to see if
	    we find a true "review" word later
Jan 30, 2019
    Spent some time evaluating "commentary" as a review word.
    Generally, looks good. There are a few exceptions to program in
    "see commentary".
    Asked Jackie and Debbie if they think 'commentary' is worth excluding.

    Added find/remove reviews functionality to sdBuild1Get.sh

Feb 4, 2019
    Cleaned up and commented featureTransform.py

    Decided I should verify my gut assumption that working with the full
    extracted text (instead of just fig legend text) would be too hard to work
    with.

    (vectorizerPlay.py)
    I tried just vectorizing the training set (40803 docs) - full extracted
    text. I thought it would run out of memory, but it didn't (actual training
    might).
    Took 1 hour, 24k features

    So if I tried to tune using the full text, it would take multiple hours per
    run.

    Just title+abs+figure legends:
    Took 4 minutes (or less?) and 3542 features

    Changed figureText.py to include *any* paragraph that includes "figure" or 
    "table". This increases the previous "only figure legend" text by about
    3.5 times. The full text is 2.5 times bigger.
    In Data/jan2/Leg_para/Proc1
    Vectorizing: 9357 features, 16 minutes

Feb 5, 2019
    Title+abs+figure paragraphs:
    preprocessed -p  removeURLsCleanStem
    running SGDlog.py on it
       Test  keep       0.75      0.87      0.81      2127
    improved precision around 10 points. Recall down a bit, but haven't tuned
    Tumor recall still around 78

    To keep all the versions of sample files straight, came up with a new
    dir structure. Need to change sdBuild* scripts to conform

    NEXT step:
	change figuretext.py to be a script itself with options (just legends,
	legends + paragraphs, legends + words)
	change sdBuild3Fig.sh to use the new figuretext.py instead of
	preprocess
	(basically separating the concepts of "informative text extraction"
	from preprocessing)

	SO have levels: 
	    sample article subset (raw or raw_no_reviews)
		what about no "mice" - depends on ref section removal
	    splitting into test/train/validation sets
	    informative text extraction
		figure text
		could include ref section removal
	    text preprocessing (featuretransform, ...)

	    (have to ponder. the boundaries get murky)

	Idea:
	    remove MGI or pubmed "reviews" from sample set
	    try figure/table legends + words in paragraphs (not whole
		paragraphs)
	    fix "cell line" transformation
	    tune from there
	Currently:
	    refactoring figureText.py to support figure legends, figure
	    paragraphs, and figure words
	Refactoring Ideas:
	    * trying different preprocessing options are not configurable,
		e.g., different fig text extraction algorithms - which
		extraction algorithm to call requires code changes.
		- should write a sampleDataLib builder that would be given
		  some option (maybe from config or cmd line) and instantiate
		  Samples from that Builder, which injects the correct object/
		  function.
		- would require a fair amount of refactoring, and should think
		  about this pattern in other places
		- postponing for now.

Feb 17, 2019
    Idea: recall for Tumor is bad because the number of Tumor papers in the
	training set is too small, it is swamped by the other samples (and
	maybe these papers are just harder to recognize.

	So try adding an additional set of papers selected for Tumor for
	the "keep_before" set. Try 1000 or so. See what happens. - changes
	to sdGetRaw.py
	Here are counts before these changes:

	Hitting database bhmgidevdb01.jax.org prod as mgd_public
	Sun Feb 17 16:44:28 2019
	    1392	Omitted references (only pm2gene indexed)
	    31163	Discard after 10/31/2017
	    21148	Keep after 10/31/2017
	    7792	Keep 10/01/2016 through 10/31/2017
	    Total time:  119.576 seconds

	Here are updated numbers w/ Tumor papers added
	Hitting database bhmgidevdb01.jax.org prod as mgd_public
	Mon Feb 18 08:32:59 2019
	   1392	Omitted references (only pm2gene indexed)
	  31163	Discard after 10/31/2017
	  21148	Keep after 10/31/2017
	   8951	Keep 10/01/2016 through 10/31/2017
		+ tumor papers from 7/1/2015
	Total time:   34.168 seconds
    Recall for papers selected by each curation group
    ap_status      selected papers:  1720 predicted keep:  1561 recall: 0.908
    gxd_status     selected papers:   176 predicted keep:   167 recall: 0.949
    go_status      selected papers:  1784 predicted keep:  1579 recall: 0.885
    tumor_status   selected papers:   142 predicted keep:   112 recall: 0.789
    qtl_status     selected papers:     3 predicted keep:     2 recall: 0.667
    Totals         selected papers:  2138 predicted keep:  1856 recall: 0.868

    So this improves recall a bit.

Feb 18, 2019
    added tumor papers back to 7/1/2013.
    Built cleanest dataset to date:
    feb18_nopmRevs (pubmed and MGI review papers removed)
    With add'l tumor papers, get recall in upper 80's. Yay!
    Sub directories:
	Legends		- just legends
	LegendsWords	- legends + 50 words around references to fig/tables
	LegendsPara	- legends + paragraphs containing refs to fig/tables

    Now we can compare the different extracted text approaches.

    To make it easier/quicker to add additional sample sets/files
    (e.g., keep_tumor), and have other files preprocessed, I rejiggered the
    build scripts to do fig text extraction and preprocessing BEFORE the
    test/val/train split. (that way, discard_after, keep_after, etc.) can be
    preprocessed once and reused as other files are added)

