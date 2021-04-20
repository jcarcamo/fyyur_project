window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};

function deleteFetchWrapper(url, redirect){
  if(confirm("Are you sure?")){
    console.log("proceed to delete");
    
    // https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
    fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    .then(response => response.json())
    .then(data => {
      // https://www.w3schools.com/howto/howto_js_redirect_webpage.asp
      window.location.replace(redirect);
    })
    .catch((error) => {
      alert("Something went wrong, please try again later.")
      console.error('Error:', error);
    });	
  }
}
