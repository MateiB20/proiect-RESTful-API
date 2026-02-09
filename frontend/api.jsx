import React, { useState, useEffect } from 'react'; 
import { createRoot } from 'react-dom/client';
import axios from 'axios';

const App = () => {
  useEffect(() => {
  const savedToken = localStorage.getItem('POSToken');
  if (savedToken) {
    setToken(savedToken);
  }
}, []);
  const [events, setEvents] = useState([]);
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
const [userRole, setUserRole] = useState("");
const [buyTicketData, setBuyTicketData] = useState({
    ticketCOD: ''
});

const handleBuyChange = (e) => {
    setBuyTicketData({
        ...buyTicketData,
        [e.target.name]: e.target.value
    });
};


  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/event-manager/events');
      setEvents(response.data.data);
    } catch (err) {
      setError("Nu s-a putut face GET");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };



const fetchPackets= async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/event-manager/event-packets');
      setEvents(response.data.data);
    } catch (err) {
      setError("Nu s-a putut face GET");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };



const fetchTickets= async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/event-manager/tickets');
      setTickets(response.data.data);
    } catch (err) {
      setError("Nu s-a putut face GET");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };



const fetchClients = async () => {
  setLoading(true);
  try {
    const response = await axios.get('http://localhost:8001/api/event-manager/clients', {
      headers: {
        'Authorization': 'Bearer '+token
      }
    });
    setClients(response.data.data);
  } catch (err) {
    setError("Nu s-a putut face GET");
    console.error(err);
  } finally {
    setLoading(false);
  }
};



const fetchEventTicket = async () => {
  setLoading(true);
  setError(null);
  try {
    const response = await axios.get("http://localhost:8000/api/event-manager/events/"+searchData.ID+"/tickets/"+searchData.COD);
    setTickets([response.data.data]);
  } catch (err) {
    setError("Nu s-a putut face GET");
    console.error(err);
  } finally {
    setLoading(false);
  }
};



const fetchPacketTicket = async () => {
  setLoading(true);
  setError(null);
  try {
    const response = await axios.get("http://localhost:8000/api/event-manager/event-packets/"+searchData.ID+"/tickets/"+searchData.COD);
    setTickets([response.data.data]);
  } catch (err) {
    setError("Nu s-a putut face GET");
    console.error(err);
  } finally {
    setLoading(false);
  }
};



const [authDataR, setAuthDataR] = useState({
    email: '',
    parola: '',
    rol:''
  });



  const handleAuthChangeR = (e) => {
    setAuthDataR({
      ...authDataR,
      [e.target.name]: e.target.value
    });
  };



  const [authDataL, setAuthDataL] = useState({
    email: '',
    parola: '',
    rol: ''
  });



  const handleAuthChangeL = (e) => {
    setAuthDataL({
      ...authDataL,
      [e.target.name]: e.target.value
    });
  };



  const [eventFormData, setEventFormData] = useState({
    ID:0,
    ID_OWNER:0,
    nume: '',
    locatie: '',
    descriere: '',
    numarLocuri: 0
  });


  const [packetFormData, setPacketFormData] = useState({
    ID: 0, 
    ID_OWNER: 0,
    nume: '', 
    locatie: '', 
    descriere: '', 
    numarLocuri: 0
});


  const handleEventChange = (e) => {
    setEventFormData({
      ...eventFormData,
      [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
  };



  const handlePacketChange = (e) => {
    setPacketFormData({
      ...packetFormData,
      [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
  };

  

const [clientFormData, setClientFormData] = useState({
  _id: '',
    email: '',
    nume: '',
    isPublic: true,
    social_media_links: [],
    lista_bilete: []
});

const [clientFormEditData, setClientFormEditData] = useState({
    nume: '',
    isPublicName: true,
    social_media_links: [],
    isPublicLink: true
});

const [ticketFormData, setTicketFormData] = useState({
    COD: "",
    PachetID: 0,
    EvenimentID: 0
});



const handleClientChange = (e) => {
    setClientFormData({
      ...clientFormData,
      [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
  }


const handleEditClientChange = (e) => {
    setClientFormEditData({
      ...clientFormEditData,
      [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
  }


  const handleTicketChange = (e) => {
    setTicketFormData({
      ...ticketFormData,
      [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
  }


const [ClientID, setClientId] = useState(null);

const fetchClientId = async (userEmail, token) => {
    try {
        const response = await axios.get(`http://localhost:8001/api/event-manager/clients/email`, {
            params: { email: userEmail },
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const id = response.data.data;
        setClientId(id);
        return id;
    } catch (error) {
        console.error("Nu s-a putut efectua obtinerea ID-ului", error.response?.data?.detail || error.message);
    }
};


const [tempSocial, setTempSocial] = useState("");
const [tempSocialPublic, setTempSocialPublic] = useState(true);
const [clients, setClients] = useState([]);
const [tickets, setTickets] = useState([]);
const [searchData, setSearchData] = useState({
    ID: 0,
    COD: ""
});
const logout = async () => {
  setLoading(true);
    try {
      const response = await axios.get('http://localhost:8001/api/event-manager/clients/'+ClientID, {
      headers: {
        'Authorization': 'Bearer '+token
      }
    });
    const user=response.data.data
        await axios.post('http://localhost:8000/api/event-manager/logout', {user}, {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
       } catch (err) {
        console.error("Eroare la logout", err);
    } finally {
  setUserRole("");
  setToken("");
  localStorage.removeItem('myAppToken');
};
}

const handleSearchChange = (e) => {
    setSearchData({
        ...searchData,
        [e.target.name]: e.target.type === 'number' ? parseInt(e.target.value, 10) || 0 : e.target.value
    });
};



  const postEvents = async () => {
    setLoading(true);
    const { ID, ...formDataPost } = eventFormData;
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.post('http://localhost:8000/api/event-manager/events', formDataPost, config);
      fetchEvents();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face POST");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const putEvents = async () => {
    setLoading(true);
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.put('http://localhost:8000/api/event-manager/events', eventFormData, config);
      fetchEvents();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const deleteEvents = async () => {
    setLoading(true);
    const { ID, ...formDataPost } = eventFormData;
    const config = {
      headers: {
        'Authorization': 'Bearer '+token
      }
    };
    try 
    {
      const response = await axios.delete('http://localhost:8000/api/event-manager/events/'+ID, config);
      fetchEvents();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face DELETE");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }



const register = async () => {
    setLoading(true);
    try
    {
       const payload = {
        _id: clientFormData._id,
        email: authDataR.email,
        prenume_nume: {
            value: clientFormData.prenume_nume,
            public: clientFormData.isPublic
        },
        social_media_links: [...clientFormData.social_media_links, { link: tempSocial, public: tempSocialPublic }],
        lista_bilete: typeof clientFormData.lista_bilete === 'string' 
        ? clientFormData.lista_bilete.split(',').map(b => b.trim()).filter(b => b !== "")
        : clientFormData.lista_bilete
    };
      const response = await axios.post('http://localhost:8000/api/event-manager/register', authDataR);
      const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
      const response2 = await axios.post('http://localhost:8001/api/event-manager/clients', payload, config);
      setToken(response.data.token);
      localStorage.setItem('POSToken', response.data.token);
    }
    catch (err)
    {
      console.error("Detalii eroare server:", err.response?.data);
    setError(err.response?.data?.detail || "Eroare server (500)");
    }
    finally
    {
      setLoading(false);
    }
  }
  


  const login = async () => {
    setLoading(true);
    try
    {
      const response = await axios.post('http://localhost:8000/api/event-manager/login', authDataL);
      setToken(response.data.token);
      setUserRole(response.data.rol || authDataL.rol);
      localStorage.setItem('POSToken', response.data.token);
      await fetchClientId(authDataL.email, response.data.token);
    }
    catch (err)
    {
      console.error("Detalii eroare server:", err.response?.data);
    setError(err.response?.data?.detail || "Eroare server (500)");
    }
    finally
    {
      setLoading(false);
    }
  }
  


  const postPackets = async () => {
    setLoading(true);
    const { ID, ...formDataPost } = packetFormData;
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.post('http://localhost:8000/api/event-manager/event-packets', formDataPost, config);
      fetchPackets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face POST");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const putPackets = async () => {
    setLoading(true);
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.put('http://localhost:8000/api/event-manager/event-packets', packetFormData, config);
      fetchPackets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const deletePackets = async () => {
    setLoading(true);
    const { COD, ...formDataPost } = packetFormData;
    const config = {
      headers: {
        'Authorization': 'Bearer '+token
      }
    };
    try 
    {
      const response = await axios.delete('http://localhost:8000/api/event-manager/event-packets/'+ID, config);
      fetchPackets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face DELETE");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }



    const postTickets = async () => {
    setLoading(true);
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.post('http://localhost:8000/api/event-manager/tickets', ticketFormData, config);
      fetchTickets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face POST");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const putTickets = async () => {
    setLoading(true);
    const config = {
      headers: {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
      }
    };
    try 
    {
      const response = await axios.put('http://localhost:8000/api/event-manager/tickets', ticketFormData, config);
      fetchTickets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const deleteTickets = async () => {
    setLoading(true);
    const { COD, ...formDataPost } = ticketFormData;
    const config = {
      headers: {
        'Authorization': 'Bearer '+token
      }
    };
    try 
    {
      const response = await axios.delete('http://localhost:8000/api/event-manager/tickets/'+COD, config);
      fetchTickets();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face DELETE");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }



  const postClients = async () => {
    setLoading(true);
    const payload = {
        _id: clientFormData._id,
        email: clientFormData.email,
        prenume_nume: {
            value: clientFormData.prenume_nume,
            public: clientFormData.isPublic
        },
        social_media_links: [...clientFormData.social_media_links, { link: tempSocial, public: tempSocialPublic }],
        lista_bilete: typeof clientFormData.lista_bilete === 'string' 
        ? clientFormData.lista_bilete.split(',').map(b => b.trim()).filter(b => b !== "")
        : clientFormData.lista_bilete
    };
    const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    try 
    {
      const response = await axios.post('http://localhost:8001/api/event-manager/clients', payload, config);
      fetchClients();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face POST");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const putClients = async () => {
  setLoading(true);
    const payload = {
      _id: clientFormData._id,
        email: clientFormData.email,
        prenume_nume: {
            value: clientFormData.prenume_nume,
            public: clientFormData.isPublic
        },
        social_media_links: [...clientFormData.social_media_links, { link: tempSocial, public: tempSocialPublic }],
        lista_bilete: typeof clientFormData.lista_bilete === 'string' 
        ? clientFormData.lista_bilete.split(',').map(b => b.trim()).filter(b => b !== "")
        : clientFormData.lista_bilete
    };
    const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    try 
    {
      const response = await axios.put('http://localhost:8001/api/event-manager/clients', payload, config);
      fetchClients();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }



  const putOwnClient = async () => {
  setLoading(true);
  const response_own_client = await axios.get(`http://localhost:8001/api/event-manager/clients/`+ClientID, {
            params: {},
            headers: { 'Authorization': 'Bearer ' + token }
        });
    const ownData = response_own_client.data.data;
    const payload = {
      _id: ClientID,
        email: ownData.email,
        prenume_nume: {
            value: clientFormEditData.nume,
            public: clientFormEditData.isPublicName
        },
        social_media_links: [...clientFormEditData.social_media_links, { link: tempSocial, public: clientFormEditData.isPublicLink }],
        lista_bilete: typeof ownData.lista_bilete === 'string' 
        ? ownData.lista_bilete.split(',').map(b => b.trim()).filter(b => b !== "")
        : ownData.lista_bilete
    };
    const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    try 
    {
      const response = await axios.put('http://localhost:8001/api/event-manager/clients', payload, config);
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }



  const deleteClients = async () => {
    setLoading(true);
    const payload = {
      _id: clientFormData._id,
        email: clientFormData.email,
        prenume_nume: {
            value: clientFormData.prenume_nume,
            public: clientFormData.isPublic
        },
        social_media_links: [...clientFormData.social_media_links, { link: tempSocial, public: tempSocialPublic }],
        lista_bilete: typeof clientFormData.lista_bilete === 'string' 
        ? clientFormData.lista_bilete.split(',').map(b => b.trim()).filter(b => b !== "")
        : clientFormData.lista_bilete
    };
    const { id, ...formDataPost } = payload;
    const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    try 
    {
      const response = await axios.delete('http://localhost:8001/api/event-manager/clients/'+id, config);
      fetchClients();
    } 
    catch (err) 
    {
      setError("Nu s-a putut face PUT");
      console.error(err);
    } 
    finally 
    {
      setLoading(false);
    }
  }

const buyTicket = async () => {
    setLoading(true);
    setError(null);
    const config = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    try {
        const response = await axios.put('http://localhost:8001/api/event-manager/clients/' + ClientID + '/tickets/'+buyTicketData.ticketCOD, {}, config);
        if (userRole === 'admin') fetchClients(); 
    } catch (err) {
        const errorMsg = err.response?.data?.detail || "Eroare la cumpararea biletului";
        setError(errorMsg);
    } finally {
        setLoading(false);
    }
};



  return (
    <div>

      <h1>Event Manager Client</h1>
      
      <button onClick={fetchEvents}>
        GET Events
      </button>
      <br/>
      <button onClick={fetchPackets}>
        GET Packets
      </button>
      <br/>
      <button onClick={fetchTickets}>
        GET Tickets
      </button>
      <br/>
      {userRole === 'admin' ? (
  <div>
      <button onClick={fetchClients}>
        GET Clients
      </button>
      </div>
) : (<p>Sunteți logat ca {userRole || 'vizitator'}. Doar administratorii pot gestiona clientii.</p>
)}

      <div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>ID_OWNER</th>
              <th>nume</th>
              <th>locatie</th>
              <th>descriere</th>
              <th>numarLocuri</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.ID}>
                <td>{event.ID}</td>
                <td>{event.ID_OWNER}</td>
                <td>{event.nume}</td>
                <td>{event.locatie}</td>
                <td>{event.descriere}</td>
                <td>{event.numarLocuri}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <table>
          <thead>
            <tr>
              <th>COD</th>
              <th>PachetID</th>
              <th>EvenimentID</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.COD}>
                <td>{ticket.COD}</td>
                <td>{ticket.PachetID}</td>
                <td>{ticket.EvenimentID}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <table>
          <thead>
            <tr>
              <th>_id</th>
              <th>Email</th>
              <th>Nume</th>
              <th>Bilete</th>
              <th>Social Media</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client._id}>
                <td>{client._id}</td>
                <td>{client.email}</td>
                <td>{client.prenume_nume?.value || "N/A"} {client.prenume_nume ? ` (${client.prenume_nume.public ? 'Public' : 'Privat'})` : ""}</td>
                <td>{client.lista_bilete?.join(", ") || "Fără bilete"}</td>
                <td>
                  {client.social_media_links?.map((s, idx) => (<div key={idx}>{s.link} ({s.public ? 'Public' : 'Privat'})</div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    <h2>Register form</h2>
      <form onSubmit={(e) => { e.preventDefault(); register(); }}>
        <input name="_id" placeholder="_id" onChange={handleClientChange}/><br/>
  <input name="prenume_nume" placeholder="Prenume nume" onChange={handleClientChange}/><br/>
  <label> Nume public? <input type="checkbox" name="isPublic" checked={clientFormData.isPublic}  onChange={(e) => setClientFormData({...clientFormData, isPublic: e.target.checked})}/></label><br/>
  <input name="social_media_links" placeholder="Social media links" onChange={(e) => setTempSocial(e.target.value)}/><br/>
  <label> Link-uri publice?<input type="checkbox"  checked={tempSocialPublic} onChange={(e) => setTempSocialPublic(e.target.checked)}></input></label><br/>
  <input name="lista_bilete" placeholder="Lista bilete" onChange={handleClientChange}/><br/>
  <input name="email" placeholder="email" onChange={handleAuthChangeR}/><br/>
  <input name="parola" placeholder="********" onChange={handleAuthChangeR}/><br/>
  <input name="rol" placeholder="rol" onChange={handleAuthChangeR}/><br/>
  <button type="submit">REGISTER</button>
    </form>



{userRole === 'client' || userRole === 'owner-event' && (
    <div>
        <h2>Editeaza profilul</h2>
        <input 
            name="nume" 
            placeholder="Nume Prenume" 
            onChange={handleEditClientChange} 
        /><br/>
        <label>
            Nume Public? 
            <input 
                type="checkbox" 
                checked={clientFormEditData.isPublicName} 
                onChange={(e) => setClientFormEditData({...clientFormEditData, isPublicName: e.target.checked})}
            />
        </label><br/>
        <input 
            placeholder="Social media links" 
            onChange={(e) => setTempSocial(e.target.value)} 
        /><br/>
        <label>
            Link Public? 
            <input 
                type="checkbox" 
                checked={clientFormEditData.isPublicLink} 
                onChange={(e) => setClientFormEditData({...clientFormEditData, isPublicLink: e.target.checked})}
            />
        </label><br/>
        <button onClick={putOwnClient}>SALVEAZA</button>
    </div>
)}



      <h2>Login form</h2>
      <form onSubmit={(e) => { e.preventDefault(); login(); }}>
  <input name="email" placeholder="email" onChange={handleAuthChangeL}/><br/>
  <input name="parola" placeholder="********" onChange={handleAuthChangeL}/><br/>
  <input name="rol" placeholder="rol" onChange={handleAuthChangeL}/><br/>
  <button type="submit">LOGIN</button>
    </form>
    <form onSubmit={(e) => { e.preventDefault(); logout(); }}>
      <button type="submit">LOGOUT</button>
    </form>
    <h2>Event form</h2>
      <form onSubmit={(e) => { e.preventDefault()}}>
  <input name="ID" type="number" placeholder="ID" onChange={handleEventChange}/><br/>
  <input name="ID_OWNER" type="number" placeholder="ID_OWNER" onChange={handleEventChange}/><br/>
  <input name="nume" placeholder="Nume" onChange={handleEventChange}/><br/>
  <input name="locatie" placeholder="Locatie" onChange={handleEventChange}/><br/>
  <input name="descriere" placeholder="Descriere" onChange={handleEventChange}/><br/>
  <input name="numarLocuri" type="number" placeholder="Locuri" onChange={handleEventChange}/><br/>
  <button type="submit" onClick={postEvents}>POST</button><br/>
  <button type="submit" onClick={putEvents}>PUT</button><br/>
  <button type="submit"  onClick={deleteEvents}>DELETE</button>
    </form>
    <h2>Packet form</h2>
    <form onSubmit={(e) => { e.preventDefault()}}>
  <input name="ID" type="number" placeholder="ID" onChange={handlePacketChange}/><br/>
  <input name="ID_OWNER" type="number" placeholder="ID_OWNER" onChange={handlePacketChange}/><br/>
  <input name="nume" placeholder="Nume" onChange={handlePacketChange}/><br/>
  <input name="locatie" placeholder="Locatie" onChange={handlePacketChange}/><br/>
  <input name="descriere" placeholder="Descriere" onChange={handlePacketChange}/><br/>
  <input name="numarLocuri" type="number" placeholder="Locuri" onChange={handlePacketChange}/><br/>
  <button type="submit" onClick={postPackets}>POST</button><br/>
  <button type="submit" onClick={putPackets}>PUT</button><br/>
  <button type="submit"  onClick={deletePackets}>DELETE</button>
    </form>
    <h2>Ticket form</h2>
      <form onSubmit={(e) => { e.preventDefault()}}>
  <input name="COD" placeholder="COD" onChange={handleTicketChange}/><br/>
  <input name="PachetID" type="number" placeholder="PachetID" onChange={handleTicketChange}/><br/>
  <input name="EvenimentID" type="number" placeholder="EvenimentID" onChange={handleTicketChange}/><br/>
  <button type="submit" onClick={postTickets}>POST</button><br/>
  <button type="submit" onClick={putTickets}>PUT</button><br/>
  <button type="submit"  onClick={deleteTickets}>DELETE</button>
    </form>
    <h2>Cumpara bilet</h2>
<form onSubmit={(e) => { e.preventDefault() }}>
    <input 
        name="ticketCOD" 
        placeholder="COD Bilet" 
        onChange={handleBuyChange} 
    /><br/>
    <button type="submit" onClick={buyTicket}>Cumpara bilet</button>
</form>
    {userRole === 'admin' ? (
  <div>
    <h2>Client Form</h2>
    <form onSubmit={(e) => { e.preventDefault()}}>
    <input name="_id" placeholder="_id" onChange={handleClientChange}/><br/>
  <input name="email" placeholder="Email" onChange={handleClientChange}/><br/>
  <input name="prenume_nume" placeholder="Prenume nume" onChange={handleClientChange}/><br/>
  <label> Nume public? <input type="checkbox" name="isPublic" checked={clientFormData.isPublic}  onChange={(e) => setClientFormData({...clientFormData, isPublic: e.target.checked})}/></label><br/>
  <input name="social_media_links" placeholder="Social media links" onChange={(e) => setTempSocial(e.target.value)}/><br/>
  <label> Link-uri publice?<input type="checkbox"  checked={tempSocialPublic} onChange={(e) => setTempSocialPublic(e.target.checked)}></input></label><br/>
  <input name="lista_bilete" placeholder="Lista bilete" onChange={handleClientChange}/><br/>
  <button type="submit" onClick={postClients}>POST</button><br/>
  <button type="submit" onClick={putClients}>PUT</button><br/>
  <button type="submit"  onClick={deleteClients}>DELETE</button>
    </form>
</div>
) : (<p>Sunteți logat ca {userRole || 'vizitator'}. Doar administratorii pot gestiona clientii.</p>
)}

  <h2>Cauta Bilet</h2>
  <form onSubmit={(e) => { e.preventDefault()}}>
  <input name="ID"  type="number" placeholder="ID (Eveniment sau Pachet)"  onChange={handleSearchChange} /><br/>
  <input name="COD"  placeholder="COD Bilet"   onChange={handleSearchChange} /><br/>
  <button onClick={fetchEventTicket}>Cauta în Evenimente</button>
  <button onClick={fetchPacketTicket}>Cauta în Pachete</button>
  </form>
</div>
  );
};

const container = document.getElementById('app');
const root = createRoot(container);
root.render(<App />);