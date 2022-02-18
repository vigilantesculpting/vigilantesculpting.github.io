%----------------------------------------------------------------------
%- Create the comment section
%----------------------------------------------------------------------

%func commentsection: post path
	<section class="commentsection">
		<section>
			<section class="commentheader">
				%set 'commentcount': post/comments ||
				%if commentcount 0 >
					<h1>Comments ({{commentcount}})</h1>
				%else
					<h1>No comments</h1>
				%end
				<p class="rsslink"><a href="{{ commentpath }}">Comment RSS Feed</a></p>
			</section>
			%# this renders the nested list of comments
			%call commentlist: 0 post/comments
		</section>
		<section>
			%call commentblurb: path
		</section>
	</section>
%end

%----------------------------------------------------------------------
%- Create a nested list of comments and replies
%----------------------------------------------------------------------

%func commentlist: depth comments
	<ul class='commentlist{{depth}}'>
	%for comment: comments
		<li class='commentitem{{depth}} commentitem'>
			%call commentitem: comment
		</li>
	%end
	</ul>
%end

%----------------------------------------------------------------------
%- Create a single comment, with its replies nested below it
%----------------------------------------------------------------------

%func commentitem: comment
	<div class='comment' id='comment{{ comment/commentid }}'>
%if comment/adminuser
		<div class="authorcomment">
%else
		<div>
%end
			<a href="#comment{{ comment/commentid }}">
				<h4>{{ comment/displayname }} said:</h4>
				<span class='commentdate'>on {{ comment/date }}</span>
			</a>
			<div>{{ comment/content }}</div>
		</div>
		%call commentlink: path comment/commentid
		%call commentlist: 1 comment/comments
	</div>
%end

%----------------------------------------------------------------------
%- Create the javascript used in the comment system
%----------------------------------------------------------------------

%func commentblurb: path
<script>
	function showReplyForm(replytoid)
	{
		var form = document.getElementById("commentform" + replytoid);
		var hideshowbutton = document.getElementById("hideshow" + replytoid);
		if (form.style.display != "grid")
		{
			form.style.display = "grid";
			hideshowbutton.innerHTML = "Cancel";
		}
		else
		{
			form.style.display = "none";
			hideshowbutton.innerHTML = "Reply";
		}
		return false; 
	}
	function newComment(pageid, replytoid)
	{
		%# create the replytouri
		var replytouri = window.location.pathname.substr(1);
		if (replytoid > 0)
			replytouri += "#comment" + replytoid;
		%# create the displayname + displayurl values
		var displayname = document.getElementById("displayname" + replytoid).value;
		if (displayname == "")
			displayname = "Anonymous"
		var displayurl = document.getElementById("displayurl" + replytoid).value;
		if (displayurl != "")
			displayurl = "(" + displayurl + ")";
		%# create the comment text
		var comment = document.getElementById("commenttext" + replytoid).value;
		var body = displayname + displayurl + " says:\n" + comment;
		%# lay out the mailto uri
		var fragment = "?subject=RE:" + encodeURIComponent(replytouri) + "&body=" + encodeURIComponent(body);
		%# set up an email to vigilante sculpting`s email address, but just obfuscate it a tad to prevent bots from sending me heaps of spam
		mydecode = function(x) { return atob(x); };
		var address = mydecode('bWFpbHRvOnZpZ2lsYW50ZXNjdWxwdGluZytjb21tZW50c0BnbWFpbC5jb20=') + fragment;
		window.open(address, '_blank');
		return false; %# do not actually go anywhere
	}
	function resetComment(replytoid)
	{
		document.getElementById("displayname" + replytoid).value = "";
		document.getElementById("displayurl" + replytoid).value = "";
		document.getElementById("commenttext" + replytoid).value = "";
		return false; %# do not actually go anywhere
	}
</script>
%call commentlink: path 0
%end

%----------------------------------------------------------------------
%- Create a comment form, to reply to the page or to a specific comment
%----------------------------------------------------------------------

%func commentlink: path replytoid
		<form name='comment{{ replytoid }}'>
			%if replytoid 0 >
				<p><button id="hideshow{{replytoid}}" onclick="return showReplyForm({{replytoid}})">Reply</button></p>
				<section class="replycomment commentform" id="commentform{{ replytoid }}">
			%else
				<h1>Add a comment</h1>
				<div>To make a comment, please send an e-mail using the form below. Comments are hand-moderated and may take a while to appear, please be patient!</div>
				<div>For general rules and site policies regarding comments, and how this works, please see 
					<a href="{{config/site_url 'blog/2022-02-15-comments_are_now_live.html' //+ }}">this post</a>
				</div>
				<div><b>Your e-mail address will never be shared.</b></div>
				<section class="commentform">
			%end
			<label class="div1 commentlabel" for="displayname{{ replytoid }}">Display name:</label>
				<input type="text" id="displayname{{ replytoid }}" placeholder="Your chosen display name" class="div2"></input>
			<label class="div3 commentlabel" for="displayurl{{ replytoid }}">Display URL:</label>
				<input type="url" id="displayurl{{ replytoid }}" placeholder="Your chosen display url" class="div4"></input>
			<label class="div5 commentlabel" for="commenttext{{ replytoid }}">Comment:</label>
				<textarea class="div6" id="commenttext{{ replytoid }}" placeholder="Your comment"></textarea>
			<div class="div7">
				<button onclick="return newComment('{{ path }}', {{ replytoid }});">Submit comment (via email)</button>
				<button onclick="return resetComment({{ replytoid }});">Reset</button>
			</div>
		</section>
	</form>
%end


