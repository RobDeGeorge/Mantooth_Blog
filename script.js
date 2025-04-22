document.addEventListener('DOMContentLoaded', function() {
    // Fetch NASA Earth Observatory Image of the Day
    fetchNASAEarthImage();
    
    // Set up a function to refresh the image once per day
    // 24 hours * 60 minutes * 60 seconds * 1000 milliseconds
    setInterval(fetchNASAEarthImage, 24 * 60 * 60 * 1000);
});

function fetchNASAEarthImage() {
    const nasaImageEl = document.getElementById('nasaImage');
    const nasaImageTitleEl = document.getElementById('nasaImageTitle');
    const nasaImageDateEl = document.querySelector('.image-date');
    const nasaReadMoreEl = document.getElementById('nasaReadMore');
    const nasaImageContainer = document.querySelector('.nasa-image-container');
    
    // Show loading state
    nasaImageEl.style.opacity = 0.5;
    nasaImageTitleEl.textContent = 'Loading NASA Earth image...';
    nasaImageDateEl.textContent = 'Date: Loading...';
    
    // NASA Earth Observatory RSS feed URL
    const rssURL = 'https://earthobservatory.nasa.gov/feeds/image-of-the-day.rss';
    
    // Using a CORS proxy to avoid cross-origin issues
    const corsProxy = 'https://cors-anywhere.herokuapp.com/';
    
    // Fetch the RSS feed
    fetch(corsProxy + rssURL)
        .then(response => response.text())
        .then(data => {
            // Parse the XML
            const parser = new DOMParser();
            const xml = parser.parseFromString(data, 'application/xml');
            
            // Get the first item (most recent)
            const item = xml.querySelector('item');
            
            // Extract the relevant data
            const title = item.querySelector('title').textContent;
            const link = item.querySelector('link').textContent;
            const pubDate = new Date(item.querySelector('pubDate').textContent);
            const description = item.querySelector('description').textContent;
            
            // Extract image URL from the description
            // This is a bit tricky as we need to parse HTML from the description
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = description;
            
            // Find the image tag in the description
            const img = tempDiv.querySelector('img');
            let imageUrl = '';
            
            if (img && img.src) {
                imageUrl = img.src;
            } else {
                // If no image is found in the description, try to find it another way
                // Earth Observatory usually includes image links that follow a pattern
                // Extract the image ID from the link
                const linkParts = link.split('/');
                const imageId = linkParts[linkParts.length - 1];
                imageUrl = `https://eoimages.gsfc.nasa.gov/images/imagerecords/${Math.floor(parseInt(imageId)/1000)*1000}/${imageId}/a-${imageId}.jpg`;
            }
            
            // Update the DOM
            nasaImageEl.src = imageUrl;
            nasaImageEl.alt = title;
            nasaImageTitleEl.textContent = title;
            nasaImageDateEl.textContent = `Date: ${pubDate.toLocaleDateString()}`;
            nasaReadMoreEl.href = link;
            
            // Update the background image of the container
            nasaImageContainer.style.setProperty('--bg-image', `url(${imageUrl})`);
            
            // Restore opacity
            nasaImageEl.style.opacity = 1;
        })
        .catch(error => {
            console.error('Error fetching NASA image:', error);
            nasaImageTitleEl.textContent = 'Could not load NASA Earth image. Please try again later.';
            nasaImageDateEl.textContent = 'Date: Unavailable';
            nasaImageEl.style.opacity = 1;
            
            // If fetch fails, use a fallback image
            nasaImageEl.src = '/Images/welcome_page.png';
            nasaImageEl.alt = 'Fallback Image';
        });
}