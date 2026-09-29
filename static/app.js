const state = {user:null,page:'feed',diagnosis:null,chatUser:null,alertTimer:null};
const $ = (selector, root=document) => root.querySelector(selector);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const formatDate = value => value ? new Date(value.includes('T') ? value : value.replace(' ', 'T') + 'Z').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}) : '';
const avatar = (user, cls='') => `<div class="avatar ${cls}">${user?.avatar ? `<img src="${escapeHtml(user.avatar)}" alt="">` : escapeHtml((user?.username||'F')[0].toUpperCase())}</div>`;
let toastTimer;
function toast(message){const el=$('#toast');el.textContent=message;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),4300)}
async function api(path,options={}){
  const response=await fetch(path,{credentials:'same-origin',...options});
  let data;try{data=await response.json()}catch{data={}}
  if(!response.ok){if(response.status===401&&state.user){state.user=null;showAuth()}throw new Error(data.message||(typeof data.detail==='string'?data.detail:`Request failed (${response.status})`))}
  return data;
}
const json=(method,body)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function showAuth(){clearInterval(state.alertTimer);$('#app-shell').hidden=true;$('#auth').hidden=false}
function showApp(){$('#auth').hidden=true;$('#app-shell').hidden=false;updateIdentity();navigate(state.page);refreshAlerts();clearInterval(state.alertTimer);state.alertTimer=setInterval(refreshAlerts,60000);loadWeather()}
function updateIdentity(){const user=state.user;$('#side-name').textContent=user.username;$('#side-place').textContent=user.place||'Add your farm';$('#side-avatar').innerHTML=user.avatar?`<img src="${escapeHtml(user.avatar)}" alt="">`:escapeHtml(user.username[0].toUpperCase())}
const pages={feed:'Community feed',planner:'Planting planner',diagnose:'Diagnose a crop',alerts:'Nearby alerts',diary:'Farm diary',messages:'Messages',profile:'My profile'};
async function navigate(page){
  if(!pages[page])return;state.page=page;$('#page-title').textContent=pages[page];$('#more-menu').hidden=true;
  document.querySelectorAll('[data-page]').forEach(button=>button.classList.toggle('active',button.dataset.page===page));
  const container=$('#page-content');container.innerHTML='<div class="card muted" style="text-align:center;padding:32px">Loading…</div>';
  try{await ({feed:renderFeed,planner:renderPlanner,diagnose:renderDiagnose,alerts:renderAlerts,diary:renderDiary,messages:renderMessages,profile:renderProfile})[page](container)}catch(error){container.innerHTML=`<div class="card">${escapeHtml(error.message)}</div>`}
}
async function loadWeather(){try{const data=await api('/api/weather');$('#weather-pill').textContent=`☀ ${data.place?data.place+' · ':''}${data.weather}`}catch{$('#weather-pill').textContent='Weather unavailable'}}
async function refreshAlerts(){if(!state.user)return;try{const data=await api('/api/alerts');const count=data.alerts.filter(a=>!a.is_read).length;const el=$('#alert-count');el.hidden=!count;el.textContent=count;if(state.page==='alerts')renderAlerts($('#page-content'))}catch{}}

function postCard(post){
  return `<article class="card feed-post">
    <div class="post-top profile-line">
      ${avatar(post)}
      <div><strong>${escapeHtml(post.username)}</strong><small>${formatDate(post.created_at)}</small></div>
    </div>
    <img class="post-photo" src="${escapeHtml(post.image)}" alt="Farm post by ${escapeHtml(post.username)}" loading="lazy">
    <div class="post-bottom">
      ${post.crop?`<span class="tag">${escapeHtml(post.crop)}</span>`:''}${post.prediction?`<span class="tag warn">${escapeHtml(post.prediction)}</span>`:''}
      <p>${escapeHtml(post.caption)}</p>
      <div class="list-actions">
        <button class="text-button like-post" data-id="${post.id}" aria-label="Like post">${post.liked_by_me?'♥':'♡'} ${post.likes_count??0}</button>
        <button class="text-button comments-post" data-id="${post.id}">💬 ${post.comments_count??0} comments</button>
        <button class="text-button profile-link" data-user="${post.user_id}">View farmer →</button>
      </div>
      <div class="comments-area" id="comments-${post.id}" hidden></div>
    </div>
  </article>`;
}

async function renderFeed(root){
  const [data,plan]=await Promise.all([api('/api/feed'),api('/api/planner')]);
  const next=plan.windows.filter(w=>w.supported).sort((a,b)=>a.days_until-b.days_until)[0];
  root.innerHTML=`<div class="grid feed-grid"><div>
    <div id="feed-list">${data.posts.length?data.posts.map(postCard).join(''):'<div class="empty"><span>🌱</span><strong>No posts yet</strong>Share the first update from your farm.</div>'}</div>
  </div><aside class="right-rail feed-rail">
    <div class="card"><h3>Next planting window</h3>
      <p class="muted">${next?`${escapeHtml(next.crop)} · ${next.in_window?'Window open':next.prepare_now?'Prepare now':`Starts ${formatDate(next.start)}`}`:'Choose crops in Profile to see your next window.'}</p>
      <button class="secondary" data-page="planner" style="margin-top:8px">View planner</button>
    </div>
    <div class="card"><h3>Find a farmer</h3>
      <label style="margin-top:8px">Search by name<input id="farmer-search" placeholder="Type a name…"></label>
      <div id="farmer-results"></div>
    </div>
  </aside></div>`;
  $('#farmer-search').addEventListener('input',debounce(async e=>{const target=$('#farmer-results');if(!e.target.value.trim()){target.innerHTML='';return}try{const data=await api(`/api/users?q=${encodeURIComponent(e.target.value)}`);target.innerHTML=data.users.length?data.users.map(user=>`<div class="search-result">${avatar(user,'small-avatar')}<strong>${escapeHtml(user.username)}</strong><button class="text-button profile-link" data-user="${user.id}">View</button></div>`).join(''):'<p class="muted small">No farmers found.</p>'}catch{}},300));
}

function debounce(fn,delay){let timer;return (...args)=>{clearTimeout(timer);timer=setTimeout(()=>fn(...args),delay)}}

async function renderPlanner(root){
  const data=await api('/api/planner');
  root.innerHTML=`<div class="grid"><div>
    <div class="page-intro"><p class="eyebrow">Looking ahead</p><h2>Plan your next season</h2><p class="muted">Windows are based on KAU crop guidance for Kerala. Check your field and current local advisory before planting.</p></div>
    ${data.windows.length?data.windows.map(window=>window.supported?`<section class="card">
      <div class="card-header"><div><p class="eyebrow">${escapeHtml(window.method)} crop</p><h3>${escapeHtml(window.crop)}</h3></div>
        <span class="tag ${window.prepare_now?'warn':''}">${window.in_window?'Window open':window.prepare_now?'Prepare now':`${window.days_until} days away`}</span></div>
      <div class="calendar-date">${formatDate(window.start)} – ${formatDate(window.end)}</div>
      <p class="muted" style="margin-top:8px">${escapeHtml(window.note)}</p>
      <a href="${escapeHtml(window.source)}" target="_blank" rel="noopener">Read KAU source ↗</a>
    </section>`:`<section class="card"><h3>${escapeHtml(window.crop)}</h3><p class="note warning-note">${escapeHtml(window.message)} No date is shown until the recommendation is verified.</p></section>`).join(''):'<div class="empty"><span>◷</span><strong>No crops selected</strong>Add your crops in Profile to see planting windows.</div>'}
  </div><aside class="right-rail">
    <div class="card"><h3>Your planner settings</h3>
      <p>${escapeHtml(state.user.crops||'No crops selected')}</p>
      <p class="muted">${state.user.irrigation?'Irrigated':'Rainfed'} · ${escapeHtml(state.user.place||'Location not set')}</p>
      <button class="secondary" data-page="profile" style="margin-top:8px">Edit farm profile</button></div>
    <div class="card"><h3>About the reminder</h3>
      <p class="muted">"Prepare now" appears during the 30 days before a planting window, and while the window is open.</p></div>
  </aside></div>`;
}

async function renderDiagnose(root){
  const crops=await api('/api/crops');
  root.innerHTML=`<div class="grid"><div>
    <div class="page-intro"><p class="eyebrow">Crop health</p><h2>Check a leaf</h2><p class="muted">Upload a clear crop photo. The result is a suggestion, not a confirmed diagnosis.</p></div>
    <div class="card"><form id="diagnose-form">
      <label>Crop<select name="crop" required>${crops.crops.map(c=>`<option value="${c.name}">${c.name}${c.available?'':' · model needed'}</option>`).join('')}</select></label>
      <label>Leaf photo<input type="file" name="image" accept="image/jpeg,image/png,image/webp" required></label>
      <div class="form-actions"><button class="primary">Analyze photo</button></div>
    </form><div id="diagnose-result"></div></div>
  </div><aside class="right-rail">
    <div class="card"><h3>How alerts work</h3><p class="muted">After a disease result, you decide whether to report it. Farmers within 5 km receive an in-app alert. Your exact location is not shared.</p></div>
    <div class="card"><h3>Model files</h3><p class="muted">${crops.crops.filter(c=>c.available).length} of ${crops.crops.length} crop models installed.</p></div>
  </aside></div>`;
  $('#diagnose-form').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;button.textContent='Analyzing…';try{const data=await api('/api/predict',{method:'POST',body:new FormData(e.target)});state.diagnosis=data;const guide=data.guidance;$('#diagnose-result').innerHTML=`<div class="result-panel"><p class="eyebrow">Suspected result · ${Math.round(data.confidence*100)}% model confidence</p><h3>${escapeHtml(data.prediction)}</h3><img class="result-photo" src="${escapeHtml(data.image)}" alt="Uploaded leaf"><h3>${escapeHtml(guide.title)}</h3><ul>${guide.steps.map(step=>`<li>${escapeHtml(step)}</li>`).join('')}</ul>${guide.source?`<a href="${escapeHtml(guide.source)}" target="_blank" rel="noopener">Review KAU source ↗</a>`:''}<p class="note warning-note">Confirm the disease with a local agricultural officer before applying treatment.</p>${guide.status!=='healthy'?`<button class="primary" id="report-disease" style="margin-top:12px">Report suspected disease to nearby farmers</button>`:''}</div>`;$('#report-disease')?.addEventListener('click',reportDisease)}catch(error){toast(error.message)}finally{button.disabled=false;button.textContent='Analyze photo'}});
}

async function reportDisease(){const button=$('#report-disease');if(!state.diagnosis)return;button.disabled=true;try{const data=await api(`/api/diagnoses/${state.diagnosis.id}/report`,{method:'POST'});button.textContent='Report sent';toast(`${data.sent} nearby farmer${data.sent===1?'':'s'} alerted`)}catch(error){toast(error.message);button.disabled=false}}

async function renderAlerts(root){
  const data=await api('/api/alerts');$('#alert-count').hidden=!data.alerts.some(a=>!a.is_read);
  root.innerHTML=`<div class="grid"><div>
    <div class="page-intro"><p class="eyebrow">Within 5 km of your farm</p><h2>Disease watch</h2><p class="muted">Community reports are suspected cases. Inspect your own crop and seek local advice before taking action.</p></div>
    ${data.alerts.length?data.alerts.map(a=>`<div class="card">
      <div class="card-header"><div><span class="tag alert">${escapeHtml(a.crop)}</span><h3>${escapeHtml(a.prediction)}</h3></div>${a.is_read?'':'<span class="tag warn">New</span>'}</div>
      <p>A farmer roughly ${a.distance_km} km from your saved farm location reported this suspected disease.</p>
      <p class="count">${formatDate(a.created_at)} · Exact location is private</p>
      ${a.is_read?'':`<button class="secondary mark-alert" data-id="${a.id}" style="margin-top:8px">Mark as read</button>`}
    </div>`).join(''):'<div class="empty"><span>◉</span><strong>No nearby alerts</strong>Reports from within 5 km will appear here.</div>'}
  </div><aside class="right-rail">
    <div class="card"><h3>Location setting</h3><p class="muted">${state.user.latitude===null?'Set your farm coordinates in Profile to receive relevant alerts.':'Your farm location is saved. Other farmers cannot see your exact coordinates.'}</p>
      <button class="secondary" data-page="profile" style="margin-top:8px">Manage location</button></div>
  </aside></div>`;
  root.querySelectorAll('.mark-alert').forEach(button=>button.addEventListener('click',async()=>{try{await api(`/api/alerts/${button.dataset.id}/read`,{method:'POST'});refreshAlerts()}catch(error){toast(error.message)}}));
}

async function renderDiary(root){
  const data=await api('/api/diary');
  root.innerHTML=`<div class="grid"><div>
    <div class="page-intro"><p class="eyebrow">Field notes</p><h2>Keep a farm diary</h2><p class="muted">Record planting, symptoms, field work, and what happened next.</p></div>
    <div class="card"><form id="diary-form">
      <div class="row"><label>Crop<select name="crop" required><option>Banana</option><option>Corn</option><option>Grapes</option></select></label><label>Date<input name="event_date" type="date" required value="${new Date().toISOString().slice(0,10)}"></label></div>
      <label>Note<textarea name="note" maxlength="1000" required placeholder="What did you plant, observe, or do?"></textarea></label>
      <div class="form-actions"><button class="primary">Save note</button></div>
    </form></div>
    <h3 class="section-title">Your notes</h3>
    ${data.entries.length?data.entries.map(entry=>`<div class="card"><span class="tag">${escapeHtml(entry.crop)}</span> <span class="count">${formatDate(entry.event_date)}</span><p style="margin-top:10px">${escapeHtml(entry.note)}</p></div>`).join(''):'<div class="empty"><span>📓</span><strong>No notes yet</strong>Start with a planting date or field observation.</div>'}
  </div></div>`;
  $('#diary-form').addEventListener('submit',async e=>{e.preventDefault();const form=e.target;try{await api('/api/diary',json('POST',Object.fromEntries(new FormData(form))));toast('Note saved');navigate('diary')}catch(error){toast(error.message)}});
}

async function renderMessages(root){
  const data=await api('/api/conversations');
  root.innerHTML=`<div class="card">
    <div class="page-intro" style="margin-bottom:14px"><p class="eyebrow">Farmer to farmer</p><h2>Messages</h2><p class="muted">Search for a farmer in the feed to start a conversation.</p></div>
    <div class="chat-layout">
      <div class="conversation-list" id="conversations">${data.users.length?data.users.map(user=>`<button data-chat="${user.id}">${escapeHtml(user.username)}</button>`).join(''):'<p class="muted small">No conversations yet.</p>'}</div>
      <div id="chat-pane"><div class="empty"><span>💬</span><strong>Choose a conversation</strong>Your messages will appear here.</div></div>
    </div>
  </div>`;
  root.querySelectorAll('[data-chat]').forEach(button=>button.addEventListener('click',()=>openChat(Number(button.dataset.chat))));
  if(state.chatUser)openChat(state.chatUser);
}

async function openChat(otherId){
  state.chatUser=otherId;if(state.page!=='messages'){await navigate('messages');return}
  try{const data=await api(`/api/messages/${otherId}`);
    $('#chat-pane').innerHTML=`<h3 style="margin-bottom:10px">${escapeHtml(data.user.username)}</h3>
      <div class="chat-thread" id="chat-thread">${data.messages.length?data.messages.map(m=>`<div class="bubble ${m.sender_id===state.user.id?'mine':''}">${escapeHtml(m.body)}<small>${formatDate(m.created_at)}</small></div>`).join(''):'<p class="muted" style="padding:12px">Say hello to start the conversation.</p>'}</div>
      <form class="chat-compose" id="chat-form"><input name="body" placeholder="Write a message" maxlength="2000" required><button class="primary">Send</button></form>`;
    $('#chat-thread').scrollTop=$('#chat-thread').scrollHeight;
    $('#chat-form').addEventListener('submit',async e=>{e.preventDefault();try{await api(`/api/messages/${otherId}`,json('POST',{body:e.target.elements.namedItem('body').value}));openChat(otherId)}catch(error){toast(error.message)}});
  }catch(error){toast(error.message)}
}

async function renderProfile(root){
  const u=state.user;const own=await api(`/api/users/${u.id}`);
  root.innerHTML=`<div class="grid"><div>
    <div class="card"><div class="profile-hero">${avatar(u)}<div><h2>${escapeHtml(u.username)}</h2><p class="muted">${escapeHtml(u.place||'Add your location')} · ${escapeHtml(u.crops||'Choose your crops')}</p></div></div>
      <form id="avatar-form"><label>Profile photo<input type="file" name="image" accept="image/jpeg,image/png,image/webp" required></label><button class="secondary">Update photo</button></form></div>
    <div class="card"><h3>Edit your farm profile</h3><form id="profile-form">
      <label>Name<input name="username" required minlength="2" value="${escapeHtml(u.username)}"></label>
      <label>Town or village<input name="place" value="${escapeHtml(u.place)}" placeholder="e.g. Kannur, Kerala"></label>
      <label>Crops you cultivate</label><div class="row crops-check">${['Banana','Corn','Grapes'].map(c=>`<label class="check"><input type="checkbox" value="${c}" ${u.crops.split(',').map(x=>x.trim()).includes(c)?'checked':''}> ${c}</label>`).join('')}</div>
      <label class="check" style="margin-top:10px"><input type="checkbox" name="irrigation" ${u.irrigation?'checked':''}> I have irrigation</label>
      <label>About your farm<textarea name="about" maxlength="600" placeholder="Tell the community what you grow">${escapeHtml(u.about)}</textarea></label>
      <h3 class="section-title">Farm location for 5 km alerts</h3>
      <p class="muted small">These coordinates are private. Set the location of your farm.</p>
      <div class="row"><label>Latitude<input name="latitude" type="number" min="-90" max="90" step="any" value="${u.latitude??''}" placeholder="e.g. 11.8745"></label><label>Longitude<input name="longitude" type="number" min="-180" max="180" step="any" value="${u.longitude??''}" placeholder="e.g. 75.3704"></label></div>
      <div class="list-actions"><button type="button" class="secondary" id="use-location">Use my current location</button><button type="button" class="text-button" id="clear-location">Remove coordinates</button></div>
      <p class="muted small">Use current location only while you are at your farm.</p>
      <div class="form-actions"><button class="primary">Save profile</button></div>
    </form></div>
    <h3 class="section-title">Your posts</h3>
    <div class="feed-compact">${own.posts.map(p=>`<img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.caption)}">`).join('')}</div>
  </div><aside class="right-rail">
    <div class="card"><h3>Your privacy</h3><p class="muted">Your name, town, crops, about text, and posts can be seen by signed-in farmers. Your phone number and farm coordinates are private.</p></div>
  </aside></div>`;
  const signOut=document.createElement('button');signOut.type='button';signOut.id='logout';signOut.className='secondary wide';signOut.textContent='Sign out';root.querySelector('.right-rail .card').appendChild(signOut);
  setupFarmMap(root,u);
  $('#avatar-form').addEventListener('submit',async e=>{e.preventDefault();try{const data=await api('/api/me/avatar',{method:'POST',body:new FormData(e.target)});state.user.avatar=data.avatar;toast('Photo updated');navigate('profile')}catch(error){toast(error.message)}});
  $('#profile-form').addEventListener('submit',async e=>{e.preventDefault();const f=e.target;const coords={latitude:f.elements.namedItem("latitude").value?Number(f.elements.namedItem("latitude").value):null,longitude:f.elements.namedItem("longitude").value?Number(f.elements.namedItem("longitude").value):null};try{state.user=await api('/api/me',json('PATCH',{username:f.elements.namedItem("username").value,place:f.elements.namedItem("place").value,about:f.elements.namedItem("about").value,crops:[...f.querySelectorAll('.crops-check input:checked')].map(x=>x.value).join(','),irrigation:f.elements.namedItem("irrigation").checked,...coords}));updateIdentity();toast('Profile saved');navigate('profile')}catch(error){toast(error.message)}});
}

function setupFarmMap(root,user){
  const form=$('#profile-form'),latInput=form.elements.namedItem('latitude'),lngInput=form.elements.namedItem('longitude'),coordinateRow=latInput.closest('.row');
  coordinateRow.hidden=true;coordinateRow.previousElementSibling.textContent='Click your farm on the map. Its exact location remains private.';$('#clear-location').textContent='Remove farm location';
  const mapElement=document.createElement('div');mapElement.id='farm-map';mapElement.setAttribute('aria-label','Select your farm location on the map');
  const status=document.createElement('p');status.id='farm-map-status';status.className='muted small';status.setAttribute('aria-live','polite');coordinateRow.before(mapElement,status);
  if(!window.L){mapElement.innerHTML='<div class="map-unavailable">Map could not load. Check your internet connection and reopen Profile.</div>';return}
  const hasSavedLocation=user.latitude!==null&&user.longitude!==null,start=hasSavedLocation?[user.latitude,user.longitude]:[10.8505,76.2711];
  const map=window.L.map(mapElement).setView(start,hasSavedLocation?15:7);let marker=null;
  window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  function setLocation(latitude,longitude,message){latInput.value=latitude.toFixed(6);lngInput.value=longitude.toFixed(6);if(marker)marker.setLatLng([latitude,longitude]);else marker=window.L.marker([latitude,longitude]).addTo(map);map.setView([latitude,longitude],15);status.textContent=message}
  if(hasSavedLocation){marker=window.L.marker(start).addTo(map);status.textContent='Your saved farm location is marked. Click elsewhere to change it.'}else status.textContent='No farm location selected yet. Click the map to place the marker.';
  map.on('click',event=>setLocation(event.latlng.lat,event.latlng.lng,'Farm location selected. Save your profile to keep it.'));
  $('#use-location').addEventListener('click',()=>{if(!navigator.geolocation)return toast('Geolocation is unavailable here');navigator.geolocation.getCurrentPosition(position=>{setLocation(position.coords.latitude,position.coords.longitude,'Current location selected. Save your profile to keep it.');toast('Current location selected')},()=>toast('Location permission was denied or unavailable'))});
  $('#clear-location').addEventListener('click',()=>{latInput.value='';lngInput.value='';if(marker){map.removeLayer(marker);marker=null}status.textContent='Farm location removed. Save your profile to confirm.'});
  setTimeout(()=>map.invalidateSize(),0);
}

async function viewUser(id){
  try{const data=await api(`/api/users/${id}`);const u=data.user;
    $('#page-title').textContent=u.username;state.page='profile';document.querySelectorAll('[data-page]').forEach(button=>button.classList.remove('active'));
    $('#page-content').innerHTML=`<div class="card">
      <div class="profile-hero">${avatar(u)}<div><h2>${escapeHtml(u.username)}</h2><p class="muted">${escapeHtml(u.place||'Farm community')} · ${escapeHtml(u.crops||'Farmer')}</p></div></div>
      <p>${escapeHtml(u.about||'No bio yet.')}</p>
      <button class="primary" id="message-user" style="margin-top:10px">Send message</button>
    </div><h3 class="section-title">Farm posts</h3>${data.posts.length?data.posts.map(postCard).join(''):'<div class="empty">No posts yet.</div>'}`;
    $('#message-user').addEventListener('click',()=>openChat(u.id));
  }catch(error){toast(error.message)}
}

function setup(){
  let registering=false;
  function authMode(value){registering=value;$('#register-fields').hidden=!value;$('#login-tab').classList.toggle('active',!value);$('#register-tab').classList.toggle('active',value);$('#auth-title').textContent=value?'Create your account':'Sign in';$('#auth-submit').textContent=value?'Create account':'Sign in';$('#auth-form').elements.namedItem('password').autocomplete=value?'new-password':'current-password'}
  $('#login-tab').addEventListener('click',()=>authMode(false));
  $('#register-tab').addEventListener('click',()=>authMode(true));

  $('#auth-form').addEventListener('submit',async e=>{e.preventDefault();const f=e.target;const button=$('#auth-submit');button.disabled=true;try{const data=registering?{username:f.elements.namedItem("username").value,phone:f.elements.namedItem("phone").value,password:f.elements.namedItem("password").value,place:f.elements.namedItem("place").value,crops:[...f.querySelectorAll('[name="crop-choice"]:checked')].map(o=>o.value).join(','),irrigation:f.elements.namedItem("irrigation").checked}:{phone:f.elements.namedItem("phone").value,password:f.elements.namedItem("password").value};state.user=await api(registering?'/api/register':'/api/login',json('POST',data));showApp()}catch(error){toast(error.message)}finally{button.disabled=false}});

  // Post composer dialog
  const dialog=$('#compose-dialog');
  $('#share-toggle').addEventListener('click',()=>dialog.showModal());
  $('#compose-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});
  $('#post-form').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;try{await api('/api/posts',{method:'POST',body:new FormData(e.target)});toast('Post published');dialog.close();e.target.reset();if(state.page==='feed')navigate('feed')}catch(error){toast(error.message)}finally{button.disabled=false}});

  document.addEventListener('click',async e=>{
    const page=e.target.closest('[data-page]');if(page){navigate(page.dataset.page);return}
    const profile=e.target.closest('.profile-link');if(profile){viewUser(Number(profile.dataset.user));return}
    const like=e.target.closest('.like-post');if(like){try{const result=await api(`/api/posts/${like.dataset.id}/like`,{method:'POST'});like.textContent=`${result.liked?'♥':'♡'} ${result.count}`}catch(error){toast(error.message)}return}
    const comments=e.target.closest('.comments-post');if(comments){const panel=$(`#comments-${comments.dataset.id}`);if(!panel)return;panel.hidden=!panel.hidden;if(!panel.hidden)loadComments(comments.dataset.id,panel)}
  });
  document.addEventListener('submit',async e=>{if(!e.target.classList.contains('comment-form'))return;e.preventDefault();const form=e.target;try{await api(`/api/posts/${form.dataset.id}/comments`,json('POST',{body:form.elements.namedItem('body').value}));loadComments(form.dataset.id,form.closest('.comments-area'))}catch(error){toast(error.message)}});
  $('#top-alerts').addEventListener('click',()=>navigate('alerts'));
  $('#mobile-more').addEventListener('click',()=>{$('#more-menu').hidden=!$('#more-menu').hidden});
  document.addEventListener('click',async e=>{if(!e.target.closest('#logout'))return;await api('/api/logout',{method:'POST'});state.user=null;state.page='feed';showAuth()});
  api('/api/me').then(user=>{state.user=user;showApp()}).catch(()=>showAuth());
}

async function loadComments(id,panel){
  try{const result=await api(`/api/posts/${id}/comments`);
    panel.innerHTML=`<div class="comment-list">${result.comments.map(c=>`<div class="comment-item"><strong>${escapeHtml(c.username)}</strong><p>${escapeHtml(c.body)}</p></div>`).join('')||'<p class="muted small" style="padding:6px 0">No comments yet.</p>'}</div><form class="chat-compose comment-form" data-id="${id}"><input name="body" maxlength="500" required placeholder="Write a comment"><button class="secondary">Post</button></form>`;
  }catch(error){toast(error.message)}
}

setup();
