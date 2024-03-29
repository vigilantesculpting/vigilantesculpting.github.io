const dialog = document.getElementById('toot-reply');

function showCommentsDialog()
{
  dialog.showModal();
}
function closeCommentsDialog()
{
  dialog.close();
}
function copyCommentsDialog(replylink)
{
  navigator.clipboard.writeText(replylink);
  dialog.close();
}

const dateOptions = {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
};

function escapeHtml(unsafe)
{
  return unsafe
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
}

function loadComments(originalpost, id, replylink)
{
// 
fetch(originalpost)
  .then(function(response)
    {
      return response.json();
    }
  )
  .then(function(data) 
    {
      if (data['descendants'] && Array.isArray(data['descendants']) && data['descendants'].length > 0)
      {
        document.getElementById('mastodon-comments-list').innerHTML = "";
        data['descendants'].forEach(
          function(reply)
          {
            reply.account.display_name = escapeHtml(reply.account.display_name);
            reply.account.reply_class = reply.in_reply_to_id == id ? "reply-original" : "reply-child";
            reply.created_date = new Date(reply.created_at);
            reply.account.emojis.forEach(emoji => {
              reply.account.display_name = reply.account.display_name.replace(`:${emoji.shortcode}:`,
                `<img src="${escapeHtml(emoji.static_url)}" alt="Emoji ${emoji.shortcode}" height="20" width="20" />`);
            });
            mastodonComment = `
<div class="mastodon-wrapper">
  <div class="comment-level ${reply.account.reply_class}"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <!-- <path d="m 307,477.17986 c -11.5,-5.1 -19,-16.6 -19,-29.2 v -64 H 176 C 78.8,383.97986 -4.6936293e-8,305.17986 -4.6936293e-8,207.97986 -4.6936293e-8,94.679854 81.5,44.079854 100.2,33.879854 c 2.5,-1.4 5.3,-1.9 8.1,-1.9 10.9,0 19.7,8.9 19.7,19.7 0,7.5 -4.3,14.4 -9.8,19.5 -9.4,8.8 -22.2,26.4 -22.2,56.700006 0,53 43,96 96,96 h 96 v -64 c 0,-12.6 7.4,-24.1 19,-29.2 11.6,-5.1 25,-3 34.4,5.4 l 160,144 c 6.7,6.2 10.6,14.8 10.6,23.9 0,9.1 -3.9,17.7 -10.6,23.8 l -160,144 c -9.4,8.5 -22.9,10.6 -34.4,5.4 z" stroke="currentColor" fill="currentColor"/ >-->
  </svg></div>
  <div class="mastodon-comment">
    <div class="comment">
      <div class="comment-avatar"><img src="${escapeHtml(reply.account.avatar_static)}" alt=""></div>
      <div class="comment-author">
        <div class="comment-author-name"><a href="${reply.account.url}" rel="nofollow">${reply.account.display_name}</a></div>
        <div class="comment-author-reply"><a href="${reply.account.url}" rel="nofollow">${escapeHtml(reply.account.acct)}</a></div>
      </div>
      <div class="comment-author-date">${reply.created_date.toLocaleString(navigator.language, dateOptions)}</div>
    </div>
    <div class="comment-content">${reply.content}</div> 
  </div>
</div>
`;
                  document.getElementById('mastodon-comments-list').appendChild(DOMPurify.sanitize(mastodonComment, {'RETURN_DOM_FRAGMENT': true}));
          }
        );
      }
      else
      {
        document.getElementById('mastodon-comments-list').innerHTML = "<p>No comments yet. Be the first to comment <a href='replylink'>here.</a></p>";
      }
    });
}
