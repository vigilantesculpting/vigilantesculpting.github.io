window.addEventListener('load', (event) => 
{

    class Radiant
    {

        constructor()
        {
            this.currentslide = null;
            this.lightboxcurrent = null;

            this.lightbox = document.getElementById('radiant-lightbox');
            this.lightbox.onmousemove = this.displayIcons;
            this.lightbox.onclick = this.clickIcons;

            this.slides = Array.from(document.getElementsByClassName('radiant-lightbox-slide'));
            for (let i = 0; i < this.slides.length; i++)
            {
                this.slides[i].onclick = this.openLightbox;
            }
            this.lightboxslot = document.getElementById('radiant-lightbox-slot');
            this.closebutton = document.getElementById('radiant-lightbox-close');
            this.prevbutton = document.getElementById('radiant-lightbox-prev');
            this.nextbutton = document.getElementById('radiant-lightbox-next');
            this.textbox = document.getElementById('radiant-lightbox-text')
        }

        calcSize = (parentWidth, parentHeight, childWidth, childHeight) =>
        {
            if (parentWidth >= childWidth && parentHeight >= childHeight)
            {
                // parent completely swallows child
                const calcWidth = childWidth;
                const calcHeight = childHeight;
                return {calcWidth, calcHeight};
            }

            // child needs to be scaled down to fit parent
            const parentAspect = parentWidth / parentHeight;
            const childAspect = childWidth / childHeight;
            if (parentAspect < childAspect)
            {
                // parent is taller than child
                const calcWidth = parentWidth;
                const calcHeight = calcWidth / childAspect;
                return {calcWidth, calcHeight};
            }
            else
            {
                // parent is shorter than child
                const calcHeight = parentHeight;
                const calcWidth = calcHeight * childAspect;
                return {calcWidth, calcHeight};
            }
        }
        calcImageSize = (img) =>
        {
            return this.calcSize(img.width, img.height, img.naturalWidth, img.naturalHeight);
        }
        calcposition = (event) =>
        {
            if (this.slides.length <= 1)
            {
                // there is only one image, we are always over it
                return 0;
            }
            // where are we in relation to the image
            let rect = this.lightbox.getBoundingClientRect();
            let x = event.clientX - rect.left;
            let y = event.clientY - rect.top;
            let imgsize = this.calcImageSize(this.lightboxcurrent);
            // first check y, if we are outside the image, return 0;
            if (y < rect.height/2 - imgsize.calcHeight/2 || y > rect.height/2 + imgsize.calcHeight/2)
                return 0;
            // otherwise check x. If we are on the image, return 0
            if (x < rect.width/2 - imgsize.calcWidth/2)
                return -1;
            if (x > rect.width/2 + imgsize.calcWidth/2)
                return 1;
            return 0;
        }
        displayIcons = (event) =>
        {
            let pos = this.calcposition(event);
            if (pos < 0)
            {
                // we are to the left of the image
                this.prevbutton.style.opacity = 1;
                this.closebutton.style.opacity = 0;
                this.nextbutton.style.opacity = 0;
            }
            else if (pos == 0)
            {
                // we are over the image
                this.prevbutton.style.opacity = 0;
                this.closebutton.style.opacity = 1;
                this.nextbutton.style.opacity = 0;
            }
            else
            {
                // we are to the right of the image
                this.prevbutton.style.opacity = 0;
                this.closebutton.style.opacity = 0;
                this.nextbutton.style.opacity = 1;
            }
        }
        clickIcons = (event) =>
        {
            let pos = this.calcposition(event);
            if (pos < 0)
                this.prevslide(event);
            else if (pos == 0)
                this.closeLightbox(event);
            else
                this.nextslide(event);
        }

        showSlide = (event) =>
        {
            if (this.currentslide instanceof HTMLImageElement)
            {
                var img = document.createElement('img');
                let src = this.currentslide.src
                if (this.currentslide.hasAttribute('data-src'))
                    src = this.currentslide.getAttribute('data-src');
                img.src = src;
                img.id = "radiant-lightbox-current-img";
                this.lightboxslot.replaceChildren(img);
                this.lightboxcurrent = img;
            }
            if (this.slides.length > 1)
            {
                this.textbox.style.opacity = 1;
                let slidenumber = this.slides.indexOf(this.currentslide) + 1;
                this.textbox.innerHTML = slidenumber + "/" + this.slides.length;
            }
        }

        openLightbox = (event) =>
        {
            this.currentslide = event.target;
            this.showSlide(event);
            this.lightbox.style.display = 'block';
        }

        closeLightbox = (event) =>
        {
            this.lightbox.style.display = 'none';
        }

        nextslide = (event) =>
        {
            let index = this.slides.indexOf(this.currentslide);
            let next = (index + 1) % this.slides.length;
            this.currentslide = this.slides[next];
            this.showSlide(event);
        }
        
        prevslide = (event) =>
        {
            let index = this.slides.indexOf(this.currentslide);
            let prev = (index - 1);
            if (prev < 0) prev = this.slides.length - 1;
            this.currentslide = this.slides[prev];
            this.showSlide(event);
        }

    }

    let radiant = new Radiant();

});
