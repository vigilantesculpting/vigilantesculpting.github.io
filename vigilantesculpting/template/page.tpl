%----------------------------------------------------------------------
%- This is the main page template
%- All pages on the site will wrap this around them
%----------------------------------------------------------------------

%func pagehead: title base_path
<!DOCTYPE html>
<html>
<head>
    <title>{{ config/title }} - {{ title }}</title>
    <meta charset="UTF-8">

%if config/debug
    <!-- Debug build -->
%else
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <!-- Note: I am only sending anonymized IP address pageviews to Google. No other information is collected! -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-RX7VS9VBWV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-RX7VS9VBWV', {'anonymize_ip': true});
    </script>
    <!-- End Google Analytics -->
%end

        <meta name="viewport" content="width=device-width">
        <link href="{{ '/' config/tgtsubdir 'favicon.ico' //+ }}" rel="icon" type="image/x-icon">
        %- CSS
        <link rel="stylesheet" type="text/css" href="{{ '/' config/tgtsubdir 'css' filekeys/css/structure.css   //+ }}">
        <link rel="stylesheet" type="text/css" href="{{ '/' config/tgtsubdir 'css' filekeys/css/style.css       //+ }}">
        <link rel="stylesheet" type="text/css" href="{{ '/' config/tgtsubdir 'css' filekeys/css/widescreen.css  //+ }}" media="screen and (min-width: 601px)" >
        %- RSS links
        <link rel="alternate"  type="application/rss+xml" href="{{ '/' config/tgtsubdir 'blog'      'rss.xml' //+  }}" title="Blog RSS Feed">
        <link rel="alternate"  type="application/rss+xml" href="{{ '/' config/tgtsubdir 'projects'  'rss.xml' //+  }}" title="Projects RSS Feed">
        <link rel="alternate"  type="application/rss+xml" href="{{ '/' config/tgtsubdir 'articles'  'rss.xml' //+  }}" title="Articles RSS Feed">
        <link rel="alternate"  type="application/rss+xml" href="{{ '/' config/tgtsubdir 'sketches'  'rss.xml' //+  }}" title="Sketches RSS Feed">
        %- Radiant lightobox
        <link rel="stylesheet" type="text/css" href="{{ '/' config/tgtsubdir 'css' filekeys/css/radiant.css    //+ }}">
        <script src="{{ '/' config/tgtsubdir 'js' filekeys/js/radiant.js //+ }}"></script>
        %- Extra links/scripts/etc, that are not body-ok
        %embed
</head>
%end

%func pagebody:
<body>
<main>

<nav>
<section class="titlesection">
    <a href="{{ '/' config/tgtsubdir //+ }}"><div class="titleimage"><img id="titleimage" src="{{ '/' config/tgtsubdir 'images' 'title.png' //+ }}" /></div></a>
    <div class="sitenavigation">
    <span class="home">
        <a href="{{ '/' config/tgtsubdir //+ }}">Home</a>
    </span>
    <span class="links">
        <a href="{{ '/' config/tgtsubdir 'blog'            //+ }}">Blog</a>
%#      <a href="{{ '/' config/tgtsubdir 'gallery'         //+ }}">Gallery</a>
        <a href="{{ '/' config/tgtsubdir 'projects'        //+ }}">Projects</a>
        <a href="{{ '/' config/tgtsubdir 'sketches'        //+ }}">Sketches</a>
%#      <a href="{{ '/' config/tgtsubdir 'wip'             //+ }}">WIP</a>
        <a href="{{ '/' config/tgtsubdir 'articles'        //+ }}">Articles</a>
        <a href="{{ '/' config/tgtsubdir 'contact.html'    //+ }}">Contact</a>
        <a href="{{ '/' config/tgtsubdir 'about.html'      //+ }}">About</a>
        <a class='highlightnav' href="{{ '/' config/tgtsubdir 'shop'             //+ }}">Shop</a>
    </span>
    </div>
</section>
</nav>

%embed

</main>

<footer>
<section>
<p>Content &copy; {{ config/current_year }} Vigilante Sculpting</p>
<p>
    <a href="https://www.artstation.com/g0rb">ArtStation</a>
    <a href="https://www.deviantart.com/gorb">DeviantArt</a>
    <a href="https://www.reddit.com/user/gorb314">Reddit</a>
    <a href="https://instagram.com/gorb314">Instagram</a>
    <a href="https://www.puttyandpaint.com/g0rb">Putty&Paint</a>
    <a href="http://www.coolminiornot.com/artist/gorb">CMON</a>
</p>
</section>
</footer>

%- lightbox
%import template/radiant.tpl

</body>
</html>
%end
