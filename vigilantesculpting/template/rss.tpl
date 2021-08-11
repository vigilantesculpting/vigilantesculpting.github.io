%----------------------------------------------------------------------
%- Functions for the RSS feeds
%----------------------------------------------------------------------

%func item: path post
	%set 'postlink': config/site_url config/tgtsubdir path (post/slug '.html' +) //+
<item>
	<title>{{ post/title }}</title>
	<link>{{ postlink }}</link>
	<description>
		<![CDATA[
		%if post/tags 'nsfw' contains
		<p><b>! NSFW !</b></p>
		%end
		<p>
		%if post/thumbnail exists
			<a class="more" href="{{ postlink }}">{{ post/thumbnail }}</a>
		%end
		{{ post/content truncate }}&nbsp;<a href="{{ postlink }}">[...Read More]</a>
		</p>
	]]>
	</description>
	<tags:taglist>
	%for tag: post/tags
		<tags:tag>{{ tag }}</tags:tag>
	%end
	</tags:taglist>
	<pubDate>{{ post/date '%%a, %%d %%b %%Y %%H:%%M:%%S %%z' strftime }}</pubDate>
</item>
%end

%func feed: title posts rsspath postpath description
%output rsspath 'rss.xml' //+
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
	xmlns="http://backend.userland.com/rss2"
	xmlns:tags="https://vigilantesculpting.github.io/tagsModule/">
<channel>
<title>{{ title }}</title>
<link>{{ config/site_url config/tgtsubdir rsspath //+ }}</link>
<description>{{ description }}</description>
%for post: posts
	%call item: postpath post
%end
</channel>
</rss>
%end
%end

%----------------------------------------------------------------------
%- Definitions for the RSS feeds
%----------------------------------------------------------------------

%set 'blogtitle':     config/title ' - Blog' +
%set 'blogdescr':     'Latest posts about sculpting, painting, drawing and model making'

%set 'projectstitle': config/title ' - Projects' +
%set 'projectsdescr': 'Latest scratchbuilt projects'

%set 'articlestitle': config/title ' - Articles' +
%set 'articlesdescr': 'Latest articles about scratchbuilding, painting, and the hobby in general'

%set 'sketchestitle': config/title ' - Sketches &amp; Drawings' +
%set 'sketchesdescr': 'Latest sketches and drawings'

%----------------------------------------------------------------------
%- Render the RSS feeds
%----------------------------------------------------------------------

%call feed: blogtitle     content/sortedblogposts 'blog'     'blog'     blogdescr
%call feed: projectstitle content/sortedprojects  'projects' 'projects' projectsdescr
%call feed: sketchestitle content/sortedsketches  'sketches' 'blog'     sketchesdescr
%call feed: articlestitle content/sortedarticles  'articles' 'blog'     articlesdescr
