%import template/page.tpl
%import template/redirect.tpl
%import template/comment.tpl

%----------------------------------------------------------------------
%- Functions for the main site
%----------------------------------------------------------------------

%func originalpost: post
	<section>
		%if 'post/puttyandpaint_url' exists
			<i><a href='{{ post/puttyandpaint_url }}'>Putty&Paint link</a></i><br />
		%end
		%if 'post/artstation_url' exists
			<i><a href='{{ post/artstation_url }}'>Artstation link</a></i><br />
		%end
		%if 'post/blogger_orig_url' exists
			<i>Originally posted on <a href="{{ post/blogger_orig_url }}">vigilantesculpting.blogspot.com</a></i><br />
		%end
		%if 'post/cmon_post_url' exists
			<i>Originally posted on <a href="{{ post/cmon_post_url }}">coolminiornot.com</a></i><br />
		%end
		%if 'post/papermodellers_post_url' exists
			<i>Originally posted on <a href="{{ post/papermodellers_post_url }}">papermodelers.com</a></i><br />
		%end
	</section>
%end

%func postsummary: postpath post
	%set 'postlink': postpath (post/slug '.html' +) //+
	<h2><a href="{{ postlink }}">{{ post/title }}</a></h2>
	<p class="meta">Published on {{ post/date '%%Y/%%m/%%d @%%H:%%M:%%S' strftime }} by <b>{{ post/author }}</b></p>
	<div class="thumbnail-container">
		%if 'post/thumbnail' exists
			<a class="more" href="{{ postlink }}">{{ post/thumbnail }}</a>
		%end
		%if post/tags 'nsfw' contains
			<p class='nsfw-warning'>NSFW / Mature Content</p>
		%end
	</div>
	<p class="summary">
		{{ post/content truncate }}&nbsp;<a class="more" href="{{ postlink }}">[...Read More]</a>
	</p>
	%call originalpost: post
%end

%func makeslides: postpath posts
	<section class="slides">
	%for post: posts
		<div class="slide">
			%call postsummary: postpath post
		</div>
	%end
	</section>
%end

%----------------------------------------------------------------------
%- Create the main index.html
%----------------------------------------------------------------------

%output 'index.html'
	%wrap pagehead: 'Home' ''
	%end
	%wrap pagebody:
		<section class="mainsection">
		<p>
		Welcome to Vigilante Sculpting. This is where I post my sculpting, scratchbuilding, drawing and painting work.
		</p>
		</section>

		%func mainslidesection: path postpath title rsstitle posts readmoretext
			<section class="mainsection">
			<div class="postnav">
				<a href="{{ path }}"><h1>{{ title }}</h1></a>
				<p class="rsslink"><a href="{{ path 'rss.xml' //+ }}">{{ rsstitle }}</a></p>
			</div>
			%call makeslides: postpath posts
			<p><a href="{{ path }}">{{ readmoretext }} &#x300B;</a></p>
			</section>
		%end

		%call mainslidesection: 'blog'     'blog'     'Latest News'                    'News RSS Feed'     content/sortedblogposts 0 3 slice 'Read latest news on the blog'
		%call mainslidesection: 'projects' 'projects' 'Latest Projects'                'Projects RSS Feed' content/sortedprojects 0 3 slice  'See more finished projects'
		%call mainslidesection: 'sketches' 'blog'     'Latest Sketches &amp; Drawings' 'Sketches RSS Feed' content/sortedsketches 0 3 slice  'See more sketches &amp; drawings'
		%call mainslidesection: 'articles' 'blog'     'Latest Articles'                'Articles RSS Feed' content/sortedarticles 0 3 slice  'Read more articles'

		%func maintextsection: path title subtitle
			<section class="mainsection">
			<a href="{{ path }}"><h2>{{ title }}</h2></a>
			<p><a href="{{ path }}">{{ subtitle }}</a></p>
			</section>
		%end

		%call maintextsection: 'contact.html' 'Contact me' 'Contact me'
		%call maintextsection: 'about.html' 'About me' 'Read more about this site and myself here'
	%end
%end

%----------------------------------------------------------------------
%- Create about and contact pages
%----------------------------------------------------------------------

%output 'about.html'
	%wrap pagehead: 'About me' ''
	%end
	%wrap pagebody:
		{{ content/about.index/content }}
		<div class="vertspacer"></div>
	%end
%end

%output 'contact.html'
	%wrap pagehead: 'Contact me' ''
	%end
	%wrap pagebody:
		{{ content/contact.index/content }}
		<div class="vertspacer"></div>
	%end
%end

%func postnavigation: postid posts name
	%if posts || 0 ==
		%exit
	%end
		<section class="postnav">
		<div class="postnav-left">
		%if postid 0 >
			%set 'firstpost': posts 0 at
			%-<a href="{{ firstpost/slug '.html' + //+ }}"><div class="nextpost">&#x300A; Latest {{ name }}</div></a>
			%-<a href="{{ firstpost/slug '.html' + //+ }}"><div class="nextpost">&#x300A;</div></a>
			<a href="latestpost.html"><div class="nextpost">&#x300A;</div></a>
			%-if postid 1 > 
				%set 'nextpost': posts (postid 1 -) at
				%-<a href="{{ nextpost/slug '.html' + //+ }}"><div class="nextpost">&#x2329; Next {{ name }}</div></a>
				<a href="{{ nextpost/slug '.html' + //+ }}" rel="next"><div class="nextpost">&#x2329;</div></a>
			%-end
		%else
			&nbsp;
		%end
		</div>
		<div class="postnav-right">
		%if postid (posts length 1 -) < 
			%-if postid (posts length 2 - ) <
				%set 'prevpost': posts (postid 1 +) at
				<a href="{{ prevpost/slug '.html' + //+ }}" rel="prev"><div class="prevpost">&#x232a;</div></a>
				%-<a href="{{ prevpost/slug '.html' + //+ }}"><div class="prevpost">Previous {{ name }} &#x232a;</div></a>
			%-end
			%set 'lastpost': posts (posts length 1 -) at
			<a href="{{ lastpost/slug '.html' + //+ }}"><div class="prevpost">&#x300B;</div></a>
			%-<a href="{{ lastpost/slug '.html' + //+ }}"><div class="prevpost">Oldest {{ name }} &#x300B;</div></a>
		%else
			&nbsp;
		%end
		</div>
		</section>
%end

%----------------------------------------------------------------------
%- Create blog post pages
%----------------------------------------------------------------------

%# outputs a blog page for each blog post in the blog/ subdirectory
%for postid post: content/sortedblogposts enumerate
	%set 'path': 'blog' post/slug '.html' + //+
	%set 'commentpath': config/site_url config/tgtsubdir 'blog' post/slug '.xml'+ //+
	%output path
		%wrap pagehead: post/title '..'
			<link rel="alternate" type="application/rss+xml" title="Comments on '{{ post/title }} - {{ config/title }}'" href="{{ commentpath }}">
		%end
		%wrap pagebody:
			<article>
				%write 'postnav'
					%call postnavigation: postid content/sortedblogposts 'post'
				%end
				%embed postnav
				<h1>{{ post/title }}</h1>
				<p class="meta">Published on {{ post/date "%%d/%%m/%%Y @%%H:%%M:%%S" strftime }} by <b>{{ post/author }}</b></p>
				<section class="mainsection">
				{{ post/content }}
				</section>
				%call originalpost: post
				<ul class="posttags">
					%for tag: post/tags
					<li>{{ tag }}</li>
					%end
				</ul>
				<div class="vertspacer"></div>
				%embed postnav
				%-%call postnavigation: postid content/sortedblogposts 'post'
			</article>
			%call commentsection: post path
		%end
	%end
%end

%func paginatenavigation: pageid pagecount basename
	%if pagecount 0 ==
		%exit
	%end
		<section class="postnav">
		<div class="postnav-left">
		%if pageid 0 >
			%set 'firstpage': basename '.html' +
			%-<a href="{{ firstpage }}"><div class="prevpage">&#x300A; First page</div></a>
			<a href="{{ firstpage }}"><div class="prevpage">&#x300A;</div></a>
			%-if pageid 1 > 
				%set 'prevpageid': pageid 1 -
				%set 'prevpage': basename prevpageid str '' prevpageid 0 > ? '.html' sum
				%-<a href="{{ prevpage }}"><div class="prevpage">&#x2329; Previous page</div></a>
				<a href="{{ prevpage }}" rel="prev"><div class="prevpage">&#x2329;</div></a>
			%-end
		%else
			&nbsp;
		%end
		</div>
		<div class="postnav-right">
		%if pageid ( pagecount 1 - ) < 
			%-if pageid ( pagecount 2 - ) < 
				%set 'nextpageid': pageid 1 + 
				%set 'nextpage': basename nextpageid str '.html' sum
				%-<a href="{{ nextpage }}"><div class="nextpage">Next page &#x232a;</div></a>
				<a href="{{ nextpage }}" rel="next"><div class="nextpage">&#x232a;</div></a>
			%-end
			%set 'lastpage': basename pagecount 1 - str '.html' sum
			%-<a href="{{ lastpage }}"><div class="nextpage">Last page &#x300B;</div></a>
			<a href="{{ lastpage }}"><div class="nextpage">&#x300B;</div></a>
		%else
			&nbsp;
		%end
		</div>
		</section>
%end

%- used for blog/index[].html, articles/index[].html, projects/index[].html and sketches/index[].html
%func makeindex: title targetdir posts postsdir description
	%set 'postgroups': posts config/paginatecount groupby
	%set 'pagecount': posts length config/paginatecount /^ int
	%for pageid postgroup: postgroups enumerate
		%output targetdir ( 'index' ( pageid str '' pageid 0 > ? ) '.html' sum ) //+
			%wrap pagehead: title '..'
			%end
			%wrap pagebody:
				<article>
					%write 'pagination'
						%call paginatenavigation: pageid pagecount 'index'
					%end
					%embed pagination

					<div class="postnav">
						<div>
							<h1>{{ title }}</h1>
							%if pagecount 1 >
								<h3>Page {{ pageid 1 + }}/{{ pagecount }}</h3>
							%end
						</div>
						<p class="rsslink"><a href="rss.xml">RSS Feed</a></p>
					</div>
					<p>{{ description }}</p>
					%call makeslides: postsdir postgroup

					<div class="vertspacer"></div>
					%embed pagination
				</article>
			%end
		%end
	%end
%end

%----------------------------------------------------------------------
%- Create the blog/ projects/ sketches & articles index pages
%----------------------------------------------------------------------

%call makeindex: 'Blog'                'blog'     content/sortedblogposts ''        content/blog.index/content
%call makeindex: 'Projects'            'projects' content/sortedprojects  ''        content/projects.index/content
%call makeindex: 'Sketches & Drawings' 'sketches' content/sortedsketches  '../blog' content/sketches.index/content
%call makeindex: 'Articles'            'articles' content/sortedarticles  '../blog' content/articles.index/content

%call makeindex: 'Shop'                'shop'     content/sortedwares     '../blog' content/shop.index/content

%- create the redirect pages, so we don't have to keep modiying older pages to get to the latest page

%output 'blog/latestpost.html'
	%call redirect: content/sortedblogposts 0 at
%end
%output 'projects/latestpost.html'
	%call redirect: content/sortedprojects 0 at
%end
%output 'sketches/latestpost.html'
	%call redirect: content/sortedsketches 0 at
%end
%output 'articles/latestpost.html'
	%call redirect: content/sortedarticles 0 at
%end
%output 'articles/latestshop.html'
	%call redirect: content/sortedwares 0 at
%end

%----------------------------------------------------------------------
%- Create the individual project pages
%----------------------------------------------------------------------

%- outputs a project/${PROJECT}[].html set for each project
%for projectid project: content/sortedprojects enumerate
	%set 'postgroups': project/posts config/paginatecount groupby
	%set 'pagecount': project/posts length config/paginatecount /^ int

	%set 'path': 'projects' project/slug '.html' + //+
	%set 'commentpath': config/site_url config/tgtsubdir 'projects' project/slug '.xml'+ //+

	%for postgroupid postgroup: postgroups enumerate
		%output 'projects' (project/slug (postgroupid str '' postgroupid 0 > ?) '.html' sum) //+
			%wrap pagehead: project/title '..'
				<link rel="alternate" type="application/rss+xml" title="Comments on '{{ project/title }} - {{ config/title }}'" href="{{ commentpath }}">
			%end
			%wrap pagebody:
				<article>
					%write 'projectsnavigate'
						%call postnavigation: projectid content/sortedprojects 'project'
					%end
					%write 'pagenavigate'
						%call paginatenavigation: postgroupid pagecount project/slug
					%end

					%embed projectsnavigate

					%if postgroupid 0 == 
						<h1>{{ project/title }}</h1>
						<p class="meta">Published on {{ project/date "%%d/%%m/%%Y @%%H:%%M:%%S" strftime }} by <b>{{ project/author }}</b></p>
						<section class="mainsection">
						{{ project/content }}
						</section>
						<ul class="posttags">
						%for tag: project/tags
							<li>{{ tag }}</li>
						%end
						</ul>
					%end

					<section class="stepxstep">
					<h2>Step by step (Steps {{ postgroupid config/paginatecount * 1 + }} thru {{ postgroupid config/paginatecount * 1 + postgroup length + 1 - }} of {{ project/posts length }})</h2>
						<p>These are the posts I made during the making of this project, in chronological order</p>
						%embed pagenavigate
							%call makeslides: '../blog' postgroup
						%embed pagenavigate
					</section>

					%embed projectsnavigate
				</article>
				%call commentsection: project path
			%end
		%end
	%end

%end

