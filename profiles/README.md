# Usage of the Template Profile

The template profile contains several `#TODO x` comments, where the `x` represents the step number this todo should be considered.
The process of profile creation requires knowledge of the data quality of both source and OSM. While we might already know the source's quality from the creation of its scraper we might not be aware of the quality of elements already present in OSM. The step-by-step template takes this into account.

## Step 1
To get a first idea of the data a minimal working profile can be created completing the variables `download_url`, `source`, `query` and `data_url`.
This profile can be executed and provides an output file which can be imported into OSM Conflator Auditor. This first audit is only superficial and meant to get a feeling for the data by looking at five to twenty elements.
You might find that OSM objects use other values than the one you used in your `query}. Adjust it if needed. If the problem is more complex than the query syntax allows, we can adjust in later in step 4 or even step 5.

## Step 2
Ideally the scraper fulfils our requirements and this step can be skipped but for now every scraper provides good data quality.
Sometimes information like the address is stored together in one tag instead of using atomic tags. For example we would have to split `addr:street_address` into `addr:street` and `addr:housenumber` as seen in Table \ref{tab:sample_input_schema}. Depending on the source other data transformations are required.

## Step 3
Depending on the brand's industry the maximum matching distance and the duplicate distance need to be adjusted. We provided default values which worked well for us. Running the OSM Conflator after adjusting these variables provides information on the potential effectiveness.

## Step 4
Sometimes the matching problem is more complex than just increasing distances. There might have been a brand takeover and the elements in OSM still use the old brand's name. Not using hard coded values would be preferred but some real world problems do not allow such luxury.

## Step 5
An alternative to step 4 and its usage of the `matches()` function is the `weight()` function. It is less flexible as it has only access to the OSM element's data. Normally this step is not needed and can be skipped.

## Step 6
This step is to polish the dataset given to OSM Conflator Auditor and to increase the comfort of the human auditor. While tags from `master_tags` will preselect values for the human auditor, the `tags.pop('tag_name')` gets rid of tags which might just pollute OSM with useless information.