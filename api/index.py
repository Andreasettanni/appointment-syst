/******************************************************************************
 * File: Dashboard.jsx
 * ----------------------------------------------------------------------------
 * Frontend React che punta al backend Flask su:
 *    appointment-syst-kykv994q5-andreasettannis-projects.vercel.app
 ******************************************************************************/
import React, { useState, useEffect } from "react";
import { Calendar, momentLocalizer } from "react-big-calendar";
import moment from "moment";
import "moment/locale/it";
import "react-big-calendar/lib/css/react-big-calendar.css";

// Importa i tuoi componenti UI reali da qui (sostituisci con i tuoi percorsi)
import {
    Alert,
    AlertDescription,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Input,
    Label,
    Table,
    TableBody,
    TableCell,
    TableHeader,
    TableRow,
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "./ui"; // Adatta il percorso

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as ReTooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from "recharts";

import {
    CalendarIcon,
    Users,
    UserPlus,
    Bell,
    Lock,
    Mail,
    Clock,
    LogOut,
    Calendar as CalendarIcon2,
    PlusCircle,
} from "lucide-react";

moment.locale("it");
const localizer = momentLocalizer(moment);

const API_URL = "https://appointment-syst-kykv994q5-andreasettannis-projects.vercel.app/api"; // URL completo del backend

// Configurazione per fetch (necessaria per CORS)
const fetchConfig = {
    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
    // Nessuna 'mode: "cors"' qui.  Il CORS va gestito nel backend
};

export { API_URL, fetchConfig };

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

function getAdminIdForUser(user) {
    return user?.role === "admin" ? user.id : user?.admin_id;
}


// --- Modale Crea Appuntamento ---
const CreateAppointmentModal = ({
    isOpen,
    onClose,
    operatori,
    clienti,
    onAddAppointment,
}) => {
   // ... (codice modale invariato)
};

// --- Modale Modifica/Elimina Appuntamento ---
const EditAppointmentModal = ({
    isOpen,
    onClose,
    appointment,
    onSave,
    onDelete,
}) => {
    // ... (codice modale invariato)
};

// --- AdminStatsPanel ---
const AdminStatsPanel = ({ operatori, appuntamenti }) => {
   // ... (codice invariato)
};

// --- Componente Dashboard ---
const Dashboard = () => {
    /*******************************************
     * Hook di stato globali
     *******************************************/
    const [view, setView] = useState("login");
    const [user, setUser] = useState(null);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    // Login
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    // Register Admin
    const [regData, setRegData] = useState({
        username: "",
        email: "",
        password: "",
        phone: "",
    });

    // Recover
    const [recoverEmail, setRecoverEmail] = useState("");

    // Admin: operatori, clienti
    const [operatori, setOperatori] = useState([]);
    const [clienti, setClienti] = useState([]);
    const [newOperator, setNewOperator] = useState({
        username: "",
        email: "",
        password: "",
        phone: "",
        specialization: "",
    });
    const [newClient, setNewClient] = useState({
        username: "",
        email: "",
        password: "",
        phone: "",
    });

    // Calendario
    const [calendarEvents, setCalendarEvents] = useState([]);
    const [appuntamenti, setAppuntamenti] = useState([]);

    // Admin Calendario
    const [adminCalendarView, setAdminCalendarView] = useState("week");
    const [adminCalendarDate, setAdminCalendarDate] = useState(new Date());

    // Operator Calendario
    const [operatorCalendarView, setOperatorCalendarView] = useState("week");
    const [operatorCalendarDate, setOperatorCalendarDate] = useState(new Date());

    // Client Calendario
    const [clientCalendarView, setClientCalendarView] = useState("week");
    const [clientCalendarDate, setClientCalendarDate] = useState(new Date());

    // Modali Appuntamenti
    const [isCreateApptOpen, setIsCreateApptOpen] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState(null);
    const [isEditApptOpen, setIsEditApptOpen] = useState(false);

    // Pending Slots (admin)
    const [pendingSlots, setPendingSlots] = useState([]);

    // Client: richiesta slot
    const [requestSlotData, setRequestSlotData] = useState({
        operator_id: "",
        day_of_week: "",
        start_time: "",
        end_time: "",
    });

    /*******************************************
     * useEffect: carica dati se user è loggato
     *******************************************/
    useEffect(() => {
        if (user?.id) {
            fetchCalendarData();
            if (user.role === "admin") {
                fetchOperatorsAndClients();
                fetchPendingSlots();
            }
        }
        // eslint-disable-next-line
    }, [user]);

    /*******************************************
     * FUNZIONI: Auth
     *******************************************/
    async function handleLogin(e) {
        e.preventDefault();
        setError("");
        setSuccess("");
        try {
            const res = await fetch(`${API_URL}/auth/login`, {
                ...fetchConfig,
                method: "POST",
                body: JSON.stringify({ username, password }),
            });

            if (!res.ok) {
                // Gestisci errori di rete e CORS
               if (res.status === 401) { // Unauthorized
                   setError("Credenziali non valide");
                } else if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                  setError("Errore di rete o CORS. Verifica la connessione al backend.");
                } else {
                  let errorData = {};
                  try {
                    errorData = await res.json()
                   } catch (jsonError) {
                      setError("Errore durante il login");
                      return;
                   }

                    setError(errorData.error || "Errore durante il login");
                }
                return; // interrompe la funzione in caso di errore
            }

            const data = await res.json();
            setUser(data.user);
            setView(data.user.role);

        } catch (err) {
            console.error("handleLogin error:", err);
            setError("Errore di rete");
        }
    }


    function handleLogout() {
        setUser(null);
        setView("login");
        setError("");
        setSuccess("");
        setUsername("");
        setPassword("");
    }

    async function handleRegister(e) {
        e.preventDefault();
        setError("");
        setSuccess("");
        try {
            const res = await fetch(`${API_URL}/auth/register`, {
                ...fetchConfig,
                method: "POST",
                body: JSON.stringify({ ...regData, role: "admin" }),
            });
               if (!res.ok) {
                // Gestisci errori di rete e CORS
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                    setError("Errore di rete o CORS durante la registrazione. Verifica la connessione al backend.");
                  } else {
                     let errorData = {};
                     try {
                        errorData = await res.json()
                     } catch (jsonError) {
                         setError("Errore durante la registrazione");
                         return;
                     }

                     setError(errorData.error || "Errore durante la registrazione");
                  }
                 return; // interrompe la funzione in caso di errore
             }

            const data = await res.json();

            setSuccess("Registrazione completata! Ora effettua il login.");
            setRegData({ username: "", email: "", password: "", phone: "" });
        } catch (err) {
            console.error("handleRegister error:", err);
            setError("Errore di rete");
        }
    }

    function handleRecover(e) {
        e.preventDefault();
        setError("");
        setSuccess("Email di recupero (finta) inviata!");
    }

    /*******************************************
     * FUNZIONI: Admin
     *******************************************/
     async function fetchOperatorsAndClients() {
        const adminId = getAdminIdForUser(user);
        if (!adminId) return;
         try {
            const [opRes, clRes] = await Promise.all([
                fetch(`${API_URL}/admin/operators/${adminId}`, fetchConfig),
                fetch(`${API_URL}/admin/clients/${adminId}`, fetchConfig),
            ]);

             if (!opRes.ok || !clRes.ok) {
                 if (opRes.type === 'opaque' || clRes.type === 'opaque' ||
                     (opRes.status === 0 && !opRes.ok) || (clRes.status === 0 && !clRes.ok)) {
                    setError("Errore di rete o CORS durante caricamento operatori/clienti. Verifica la connessione al backend.");
                } else {
                   let opData = {};
                   let clData = {};
                     try {
                        opData = opRes.ok ? await opRes.json() : {error: "Errore caricamento operatori"};
                        clData = clRes.ok ? await clRes.json() : {error: "Errore caricamento clienti"};
                     } catch (jsonError) {
                        setError("Errore durante il caricamento operatori/clienti")
                         return;
                     }


                   setError(opData.error || clData.error || "Errore caricamento operatori/clienti");
                }
                return; // interrompe la funzione in caso di errore
            }
            const opData = await opRes.json();
            const clData = await clRes.json();

            setOperatori(opData.operators || []);
            setClienti(clData.clients || []);


        } catch (err) {
            console.error("fetchOperatorsAndClients error:", err);
            setError("Errore di rete");
        }
    }

    async function fetchPendingSlots() {
        setError("");
         try {
            const res = await fetch(`${API_URL}/admin/slots/pending`, fetchConfig);
            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                     setError("Errore di rete o CORS durante caricamento slot pendenti. Verifica la connessione al backend.");
                } else {
                    let errorData = {};
                     try {
                        errorData = await res.json()
                      } catch (jsonError) {
                          setError("Errore durante il caricamento slot pendenti")
                          return;
                      }
                   setError(errorData.error || "Errore caricamento slot pendenti");
                }
                 return; // interrompe la funzione in caso di errore
            }

             const data = await res.json();
            setPendingSlots(data.slots || []);
        } catch (err) {
            console.error("fetchPendingSlots error:", err);
            setError("Errore di rete");
        }
    }

    async function handleApproveSlot(slotId) {
         setError("");
         setSuccess("");
         try {
            const res = await fetch(`${API_URL}/admin/slots/${slotId}/approve`, {
                ...fetchConfig,
                method: "PUT",
            });
            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                     setError("Errore di rete o CORS durante approvazione slot. Verifica la connessione al backend.");
                 } else {
                    let errorData = {};
                      try {
                         errorData = await res.json();
                      } catch (jsonError) {
                         setError("Errore durante approvazione slot")
                          return;
                     }
                    setError(errorData.error || "Errore approvazione slot");
                 }
                  return; // interrompe la funzione in caso di errore
            }
            const data = await res.json();
            setSuccess("Slot approvato con successo!");
            fetchPendingSlots();
            fetchCalendarData();
        } catch (err) {
            console.error("handleApproveSlot error:", err);
            setError("Errore di rete");
        }
    }

    async function handleRejectSlot(slotId) {
        setError("");
        setSuccess("");
         try {
            const res = await fetch(`${API_URL}/admin/slots/${slotId}/reject`, {
                 ...fetchConfig,
                method: "PUT",
            });
            if (!res.ok) {
                 if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                   setError("Errore di rete o CORS durante rifiuto slot. Verifica la connessione al backend.");
                 } else {
                    let errorData = {};
                    try {
                      errorData = await res.json();
                    } catch (jsonError) {
                        setError("Errore durante rifiuto slot")
                          return;
                    }
                   setError(errorData.error || "Errore rifiuto slot");
                 }
                  return; // interrompe la funzione in caso di errore
            }

            const data = await res.json();
            setSuccess("Slot rifiutato");
            fetchPendingSlots();
            fetchCalendarData();
        } catch (err) {
            console.error("handleRejectSlot error:", err);
            setError("Errore di rete");
        }
    }

    async function handleAddOperator(e) {
         e.preventDefault();
        setError("");
        setSuccess("");
        const adminId = getAdminIdForUser(user);
        if (!adminId) return;
         try {
            const res = await fetch(`${API_URL}/admin/operators/add`, {
                 ...fetchConfig,
                 method: "POST",
                 body: JSON.stringify({ admin_id: adminId, ...newOperator }),
            });
           if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                   setError("Errore di rete o CORS durante creazione operatore. Verifica la connessione al backend.");
                 } else {
                    let errorData = {};
                     try {
                        errorData = await res.json()
                     } catch (jsonError) {
                         setError("Errore durante la creazione dell'operatore")
                         return;
                     }
                   setError(errorData.error || "Errore creazione operatore");
                 }
                return; // interrompe la funzione in caso di errore
           }

            const data = await res.json();

            setSuccess("Operatore creato con successo!");
            setNewOperator({
                username: "",
                email: "",
                password: "",
                phone: "",
                specialization: "",
            });
            fetchOperatorsAndClients();
        } catch (err) {
            console.error("handleAddOperator error:", err);
            setError("Errore di rete");
        }
    }

     async function handleAddClient(e) {
        e.preventDefault();
        setError("");
        setSuccess("");
        const adminId = getAdminIdForUser(user);
        if (!adminId) return;
        try {
            const res = await fetch(`${API_URL}/auth/register`, {
                ...fetchConfig,
                method: "POST",
                body: JSON.stringify({
                    ...newClient,
                    role: "client",
                    admin_id: adminId,
                }),
            });

            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                    setError("Errore di rete o CORS durante creazione cliente. Verifica la connessione al backend.");
                 } else {
                     let errorData = {};
                       try {
                          errorData = await res.json()
                        } catch (jsonError) {
                          setError("Errore durante la creazione del cliente")
                           return;
                         }
                    setError(errorData.error || "Errore creazione cliente");
                }
                return; // interrompe la funzione in caso di errore
            }
            const data = await res.json();

            setSuccess("Cliente creato con successo!");
            setNewClient({ username: "", email: "", password: "", phone: "" });
            fetchOperatorsAndClients();
        } catch (err) {
            console.error("handleAddClient error:", err);
            setError("Errore di rete");
        }
    }


    async function handleAddAppointment(formData) {
         setError("");
         setSuccess("");
         try {
             const res = await fetch(`${API_URL}/admin/appointments`, {
                 ...fetchConfig,
                method: "POST",
                 body: JSON.stringify(formData),
             });
             if (!res.ok) {
                 if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                      setError("Errore di rete o CORS durante creazione appuntamento. Verifica la connessione al backend.");
                 } else {
                     let errorData = {};
                       try {
                            errorData = await res.json()
                        } catch (jsonError) {
                           setError("Errore durante la creazione dell'appuntamento");
                            return;
                        }
                     setError(errorData.error || "Errore creazione appuntamento");
                 }
                  return; // interrompe la funzione in caso di errore
             }
             const data = await res.json();
             setSuccess("Appuntamento creato con successo!");
             fetchCalendarData();
         } catch (err) {
            console.error("handleAddAppointment error:", err);
            setError("Errore di rete");
         }
    }

    async function handleSaveAppointment(formData) {
         setError("");
         setSuccess("");
         try {
             const { id, ...updates } = formData;
             updates.start_time = moment(updates.start_time).toISOString();
             updates.end_time = moment(updates.end_time).toISOString();
             const res = await fetch(`${API_URL}/admin/appointments/${id}`, {
                ...fetchConfig,
                method: "PUT",
                 body: JSON.stringify(updates),
             });
            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                    setError("Errore di rete o CORS durante aggiornamento appuntamento. Verifica la connessione al backend.");
                } else {
                    let errorData = {};
                      try {
                         errorData = await res.json()
                      } catch (jsonError) {
                           setError("Errore durante l'aggiornamento dell'appuntamento")
                            return;
                     }
                   setError(errorData.error || "Errore update appuntamento");
                 }
                  return; // interrompe la funzione in caso di errore
            }

            const data = await res.json();
            setSuccess("Appuntamento aggiornato!");
            fetchCalendarData();
         } catch (err) {
             console.error("handleSaveAppointment error:", err);
             setError("Errore di rete");
         }
    }

    async function handleDeleteAppointment(apptId) {
        setError("");
         setSuccess("");
        try {
            const res = await fetch(`${API_URL}/admin/appointments/${apptId}`, {
                 ...fetchConfig,
                method: "DELETE",
            });

            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                     setError("Errore di rete o CORS durante eliminazione appuntamento. Verifica la connessione al backend.");
                 } else {
                      let errorData = {};
                        try {
                          errorData = await res.json();
                       } catch (jsonError) {
                           setError("Errore durante l'eliminazione dell'appuntamento");
                            return;
                        }

                   setError(errorData.error || "Errore eliminazione appuntamento");
                 }
                return; // interrompe la funzione in caso di errore
            }

             const data = await res.json();

             setSuccess("Appuntamento eliminato!");
             fetchCalendarData();
        } catch (err) {
            console.error("handleDeleteAppointment error:", err);
            setError("Errore di rete");
        }
    }

    async function handleWhatsAppReminders() {
       setError("");
       setSuccess("");
        try {
            const res = await fetch(`${API_URL}/admin/send-reminders`, {
                 ...fetchConfig,
                method: "POST",
            });
            if (!res.ok) {
                 if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                     setError("Errore di rete o CORS durante invio notifiche. Verifica la connessione al backend.");
                 } else {
                      let errorData = {};
                      try {
                        errorData = await res.json();
                      } catch (jsonError) {
                         setError("Errore durante l'invio delle notifiche")
                           return;
                     }

                     setError(data.error || "Errore invio notifiche");
                 }
                 return; // interrompe la funzione in caso di errore
             }

             const data = await res.json();
             setSuccess("Notifiche WhatsApp inviate con successo!");
        } catch (err) {
             console.error("handleWhatsAppReminders error:", err);
             setError("Errore di rete");
        }
    }

    /*******************************************
     * FUNZIONI: Calendario
     *******************************************/
    async function fetchCalendarData() {
         if (!user?.id) return;
        try {
             const res = await fetch(`${API_URL}/calendar/${user.id}`, fetchConfig);
            if (!res.ok) {
                 if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                   setError("Errore di rete o CORS durante caricamento calendario. Verifica la connessione al backend.");
                 } else {
                   let errorData = {};
                     try{
                        errorData = await res.json()
                     } catch (jsonError) {
                           setError("Errore durante il caricamento del calendario")
                          return;
                     }
                   setError(errorData.error || "Errore caricamento calendario");
                 }
                  return; // interrompe la funzione in caso di errore
            }
            const data = await res.json();
             // Mappa i campi start_time ed end_time in oggetti Date
            const mapped = data.events.map((ev) => ({
                ...ev,
                start: new Date(ev.start_time),
                end: new Date(ev.end_time),
                isSlot: ev.type === "slot",
                slotStatus: ev.status,
            }));
            setCalendarEvents(mapped);

             // Se admin, estrai gli appuntamenti per pannello statistiche
            if (user.role === "admin") {
                const apps = mapped
                    .filter((m) => !m.isSlot)
                    .map((a) => ({
                        id: a.id,
                        operator_id: a.operator_id,
                        client_id: a.client_id,
                        start_time: a.start,
                        end_time: a.end,
                        service_type: a.service_type,
                        status: a.status,
                    }));
                 setAppuntamenti(apps);
             }
         } catch (err) {
            console.error("fetchCalendarData error:", err);
            setError("Errore di rete");
        }
    }

    /*******************************************
     * FUNZIONI: Client - crea richiesta slot
     *******************************************/
    async function handleRequestSlot(e) {
         e.preventDefault();
         setError("");
         setSuccess("");
         if (!user?.id) return;
         try {
             const res = await fetch(`${API_URL}/client/slots/request`, {
                 ...fetchConfig,
                 method: "POST",
                 body: JSON.stringify({
                     ...requestSlotData,
                     client_id: user.id,
                 }),
             });
            if (!res.ok) {
                if (res.type === 'opaque' || (res.status === 0 && !res.ok)) {
                    setError("Errore di rete o CORS durante richiesta slot. Verifica la connessione al backend.");
                 } else {
                      let errorData = {};
                       try {
                            errorData = await res.json()
                        } catch (jsonError) {
                            setError("Errore durante l'invio della richiesta slot")
                          return;
                       }
                    setError(errorData.error || "Errore invio richiesta slot");
                 }
                  return; // interrompe la funzione in caso di errore
            }
            const data = await res.json();

             setSuccess("Richiesta slot inviata! Attendi approvazione dall'admin.");
             setRequestSlotData({
                 operator_id: "",
                 day_of_week: "",
                 start_time: "",
                 end_time: "",
             });
         } catch (err) {
            console.error("handleRequestSlot error:", err);
            setError("Errore di rete");
         }
    }


    /*******************************************
     * RENDER: login, register, recover
     *******************************************/
    function renderLogin() {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Lock className="h-4 w-4" />
                            Login
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div>
                                <Label>Username</Label>
                                <Input
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                />
                            </div>
                            <div>
                                <Label>Password</Label>
                                <Input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                            {error && (
                                <Alert variant="destructive">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            {success && (
                                <Alert>
                                    <AlertDescription>{success}</AlertDescription>
                                </Alert>
                            )}
                            <Button type="submit" className="w-full">
                                Accedi
                            </Button>
                        </form>
                        <div className="mt-4 text-center space-x-4">
                            <Button variant="link" onClick={() => setView("recover")}>
                                Recupera Password
                            </Button>
                            <Button variant="link" onClick={() => setView("register")}>
                                Registrazione Admin
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    function renderRegister() {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <UserPlus className="h-4 w-4" />
                            Registrazione Admin
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div>
                                <Label>Username</Label>
                                <Input
                                    value={regData.username}
                                    onChange={(e) =>
                                        setRegData({ ...regData, username: e.target.value })
                                    }
                                    required
                                />
                            </div>
                            <div>
                                <Label>Email</Label>
                                <Input
                                    type="email"
                                    value={regData.email}
                                    onChange={(e) =>
                                        setRegData({ ...regData, email: e.target.value })
                                    }
                                    required
                                />
                            </div>
                            <div>
                                <Label>Password</Label>
                                <Input
                                    type="password"
                                    value={regData.password}
                                    onChange={(e) =>
                                        setRegData({ ...regData, password: e.target.value })
                                    }
                                    required
                                />
                            </div>
                            <div>
                                <Label>Telefono</Label>
                                <Input
                                    value={regData.phone}
                                    onChange={(e) =>
                                        setRegData({ ...regData, phone: e.target.value })
                                    }
                                />
                            </div>
                            {error && (
                                <Alert variant="destructive">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            {success && (
                                <Alert>
                                    <AlertDescription>{success}</AlertDescription>
                                </Alert>
                            )}
                            <Button type="submit" className="w-full">
                                Registrati
                            </Button>
                        </form>
                        <div className="mt-4 text-center">
                            <Button variant="link" onClick={() => setView("login")}>
                                Torna al Login
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    function renderRecover() {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Mail className="h-4 w-4" />
                            Recupero Password
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleRecover} className="space-y-4">
                            <div>
                                <Label>Email</Label>
                                <Input
                                    type="email"
                                    value={recoverEmail}
                                    onChange={(e) => setRecoverEmail(e.target.value)}
                                    required
                                />
                            </div>
                            {error && (
                                <Alert variant="destructive">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            {success && (
                                <Alert>
                                    <AlertDescription>{success}</AlertDescription>
                                </Alert>
                            )}
                            <Button type="submit" className="w-full">
                                Invia Richiesta
                            </Button>
                        </form>
                        <div className="mt-4 text-center">
                            <Button variant="link" onClick={() => setView("login")}>
                                Torna al Login
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    /*******************************************
     * RENDER: ADMIN
     *******************************************/
    function renderAdmin() {
        // Quando clicco su un evento nel calendario admin
        function handleSelectAdminEvent(ev) {
            if (!ev.isSlot) {
                setSelectedAppointment(ev);
                setIsEditApptOpen(true);
            }
        }

        return (
            <div className="p-4 md:p-6 max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <h1 className="text-3xl font-bold">Dashboard Admin</h1>
                    <div className="space-x-2 flex flex-wrap">
                        <Button onClick={handleWhatsAppReminders}>
                            <Bell className="h-4 w-4 mr-2" />
                            Invia Notifiche
                        </Button>
                        <Button variant="destructive" onClick={handleLogout}>
                            <LogOut className="h-4 w-4 mr-2" />
                            Logout
                        </Button>
                    </div>
                </div>

                                {/* Pannello statistiche */}
                <AdminStatsPanel operatori={operatori} appuntamenti={appuntamenti} />

                {/* Tabs */}
                <Tabs defaultValue="operatori" className="mt-6">
                    <TabsList>
                        <TabsTrigger value="operatori">
                            <Users className="h-4 w-4 mr-2" />
                            Operatori
                        </TabsTrigger>
                        <TabsTrigger value="clienti">
                            <UserPlus className="h-4 w-4 mr-2" />
                            Clienti
                        </TabsTrigger>
                        <TabsTrigger value="appuntamenti">
                            <CalendarIcon className="h-4 w-4 mr-2" />
                            Appuntamenti
                        </TabsTrigger>
                        <TabsTrigger value="pendingSlots">
                            <Clock className="h-4 w-4 mr-2" />
                            Richieste Slot
                        </TabsTrigger>
                    </TabsList>

                    {/* OPERATORI */}
                    <TabsContent value="operatori">
                        <Card>
                            <CardHeader>
                                <CardTitle>Gestione Operatori</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleAddOperator} className="space-y-4 mb-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label>Username</Label>
                                            <Input
                                                value={newOperator.username}
                                                onChange={(e) =>
                                                    setNewOperator({ ...newOperator, username: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Email</Label>
                                            <Input
                                                type="email"
                                                value={newOperator.email}
                                                onChange={(e) =>
                                                    setNewOperator({ ...newOperator, email: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Password</Label>
                                            <Input
                                                type="password"
                                                value={newOperator.password}
                                                onChange={(e) =>
                                                    setNewOperator({ ...newOperator, password: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Telefono</Label>
                                            <Input
                                                value={newOperator.phone}
                                                onChange={(e) =>
                                                    setNewOperator({ ...newOperator, phone: e.target.value })
                                                }
                                            />
                                        </div>
                                        <div className="col-span-2">
                                            <Label>Specializzazione</Label>
                                            <Input
                                                value={newOperator.specialization}
                                                onChange={(e) =>
                                                    setNewOperator({
                                                        ...newOperator,
                                                        specialization: e.target.value,
                                                    })
                                                }
                                            />
                                        </div>
                                    </div>
                                    <Button type="submit">Aggiungi Operatore</Button>
                                </form>

                                {/* Lista Operatori */}
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableCell>Username</TableCell>
                                            <TableCell>Email</TableCell>
                                            <TableCell>Telefono</TableCell>
                                            <TableCell>Specializzazione</TableCell>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {operatori.map((op) => (
                                            <TableRow key={op.id}>
                                                <TableCell>{op.username}</TableCell>
                                                <TableCell>{op.email}</TableCell>
                                                <TableCell>{op.phone}</TableCell>
                                                <TableCell>{op.specialization}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* CLIENTI */}
                    <TabsContent value="clienti">
                        <Card>
                            <CardHeader>
                                <CardTitle>Gestione Clienti</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleAddClient} className="space-y-4 mb-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label>Username</Label>
                                            <Input
                                                value={newClient.username}
                                                onChange={(e) =>
                                                    setNewClient({ ...newClient, username: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Email</Label>
                                            <Input
                                                type="email"
                                                value={newClient.email}
                                                onChange={(e) =>
                                                    setNewClient({ ...newClient, email: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Password</Label>
                                            <Input
                                                type="password"
                                                value={newClient.password}
                                                onChange={(e) =>
                                                    setNewClient({ ...newClient, password: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label>Telefono</Label>
                                            <Input
                                                value={newClient.phone}
                                                onChange={(e) =>
                                                    setNewClient({ ...newClient, phone: e.target.value })
                                                }
                                            />
                                        </div>
                                    </div>
                                    <Button type="submit">Aggiungi Cliente</Button>
                                </form>

                                {/* Lista Clienti */}
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableCell>Username</TableCell>
                                            <TableCell>Email</TableCell>
                                            <TableCell>Telefono</TableCell>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {clienti.map((c) => (
                                            <TableRow key={c.id}>
                                                <TableCell>{c.username}</TableCell>
                                                <TableCell>{c.email}</TableCell>
                                                <TableCell>{c.phone}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* APPUNTAMENTI */}
                    <TabsContent value="appuntamenti">
                        <Card>
                            <CardHeader>
                                <CardTitle>Calendario (Slot + Appuntamenti)</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="mb-4">
                                    <Button onClick={() => setIsCreateApptOpen(true)}>
                                        <CalendarIcon2 className="h-4 w-4 mr-2" />
                                        Nuovo Appuntamento
                                    </Button>
                                </div>
                                <Calendar
                                    localizer={localizer}
                                    events={calendarEvents}
                                    startAccessor="start"
                                    endAccessor="end"
                                    view={adminCalendarView}
                                    onView={(v) => setAdminCalendarView(v)}
                                    views={["month", "week", "day"]}
                                    date={adminCalendarDate}
                                    onNavigate={(dateObj) => setAdminCalendarDate(dateObj)}
                                    style={{ height: 600 }}
                                    messages={{
                                        next: "Successivo",
                                        previous: "Precedente",
                                        today: "Oggi",
                                        month: "Mese",
                                        week: "Settimana",
                                        day: "Giorno",
                                    }}
                                    tooltipAccessor={(event) => {
                                        if (event.isSlot) {
                                            return `Slot ${event.slotStatus} (Operatore: ${event.operator_name})`;
                                        }
                                        return `Appuntamento con ${event.clientName}`;
                                    }}
                                    eventPropGetter={(event) => {
                                        if (event.isSlot) {
                                            if (event.slotStatus === "approved") {
                                                return { style: { backgroundColor: "#F59E0B" } };
                                            }
                                            if (event.slotStatus === "pending") {
                                                return { style: { backgroundColor: "#9CA3AF" } };
                                            }
                                            return { style: { backgroundColor: "#6B7280" } };
                                        }
                                        // Appuntamento
                                        let bg = "#3B82F6";
                                        if (event.status === "completed") bg = "#10B981";
                                        else if (event.status === "cancelled") bg = "#EF4444";
                                        return { style: { backgroundColor: bg } };
                                    }}
                                    onSelectEvent={handleSelectAdminEvent}
                                />
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* SLOT PENDING */}
                    <TabsContent value="pendingSlots">
                        <Card>
                            <CardHeader>
                                <CardTitle>Richieste Slot (da Approvare)</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableCell>ID</TableCell>
                                            <TableCell>Operatore</TableCell>
                                            <TableCell>Giorno</TableCell>
                                            <TableCell>Orario</TableCell>
                                            <TableCell>Cliente</TableCell>
                                            <TableCell>Azioni</TableCell>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {pendingSlots.map((slot) => (
                                            <TableRow key={slot.id}>
                                                <TableCell>{slot.id}</TableCell>
                                                <TableCell>{slot.operator_id}</TableCell>
                                                <TableCell>{slot.day_of_week}</TableCell>
                                                <TableCell>
                                                    {slot.start_time} - {slot.end_time}
                                                </TableCell>
                                                <TableCell>{slot.client_id}</TableCell>
                                                <TableCell>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => handleApproveSlot(slot.id)}
                                                        className="mr-2"
                                                    >
                                                        Approva
                                                    </Button>
                                                    <Button
                                                        variant="destructive"
                                                        size="sm"
                                                        onClick={() => handleRejectSlot(slot.id)}
                                                    >
                                                        Rifiuta
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>

                 {/* Modali Appuntamenti */}
                <CreateAppointmentModal
                    isOpen={isCreateApptOpen}
                    onClose={() => setIsCreateApptOpen(false)}
                    operatori={operatori}
                    clienti={clienti}
                    onAddAppointment={handleAddAppointment}
                />
                <EditAppointmentModal
                    isOpen={isEditApptOpen}
                    onClose={() => setIsEditApptOpen(false)}
                    appointment={selectedAppointment}
                    onSave={handleSaveAppointment}
                    onDelete={handleDeleteAppointment}
                />


                {error && (
                    <Alert variant="destructive" className="mt-4">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                {success && (
                    <Alert className="mt-4">
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}
            </div>
        );
    }

    /*******************************************
     * RENDER: OPERATOR
     *******************************************/
    function renderOperator() {
        function handleSelectOperatorEvent(ev) {
            // ...
        }

        return (
            <div className="p-4 md:p-6 max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <h1 className="text-3xl font-bold">Dashboard Operatore</h1>
                    <Button variant="destructive" onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Logout
                    </Button>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Calendario (Slot + Appuntamenti)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Calendar
                            localizer={localizer}
                            events={calendarEvents}
                            startAccessor="start"
                            endAccessor="end"
                            view={operatorCalendarView}
                            onView={(v) => setOperatorCalendarView(v)}
                            views={["month", "week", "day"]}
                            date={operatorCalendarDate}
                            onNavigate={(dateObj) => setOperatorCalendarDate(dateObj)}
                            style={{ height: 600 }}
                            messages={{
                                next: "Successivo",
                                previous: "Precedente",
                                today: "Oggi",
                                month: "Mese",
                                week: "Settimana",
                                day: "Giorno",
                            }}
                             tooltipAccessor={(event) => {
                                if (event.isSlot) {
                                    return `Slot ${event.slotStatus} (Operatore: ${event.operator_name})`;
                                }
                                return `Appuntamento con ${event.clientName}`;
                            }}
                            eventPropGetter={(event) => {
                                if (event.isSlot) {
                                    if (event.slotStatus === "approved") {
                                        return { style: { backgroundColor: "#F59E0B" } };
                                    } else if (event.slotStatus === "pending") {
                                        return { style: { backgroundColor: "#9CA3AF" } };
                                    }
                                    return { style: { backgroundColor: "#6B7280" } };
                                }
                                let bg = "#3B82F6";
                                if (event.status === "completed") bg = "#10B981";
                                else if (event.status === "cancelled") bg = "#EF4444";
                                return { style: { backgroundColor: bg } };
                            }}
                            onSelectEvent={handleSelectOperatorEvent}
                        />
                    </CardContent>
                </Card>

                {error && (
                    <Alert variant="destructive" className="mt-4">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                {success && (
                    <Alert className="mt-4">
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}
            </div>
        );
    }

    /*******************************************
     * RENDER: CLIENT
     *******************************************/
    function renderClient() {
        function handleSelectClientEvent(ev) {
            // se volevi "prenotare" uno slot, potresti gestire qui
        }

        return (
            <div className="p-4 md:p-6 max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <h1 className="text-3xl font-bold">Dashboard Cliente</h1>
                    <Button variant="destructive" onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Logout
                    </Button>
                </div>

                {/* Richiesta Slot */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>Crea Richiesta Slot</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleRequestSlot} className="space-y-4">
                            <div>
                                <Label>Operatore</Label>
                                <Select
                                    onValueChange={(val) =>
                                        setRequestSlotData({ ...requestSlotData, operator_id: val })
                                    }
                                    value={requestSlotData.operator_id}
                                    required
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Seleziona Operatore" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {operatori.map((op) => (
                                            <SelectItem key={op.id} value={op.id.toString()}>
                                                {op.username}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label>Giorno (1=Lun,2=Mar,...,0=Dom)</Label>
                                <Select
                                    onValueChange={(val) =>
                                        setRequestSlotData({ ...requestSlotData, day_of_week: val })
                                    }
                                    value={requestSlotData.day_of_week}
                                    required
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Giorno" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="1">Lunedì</SelectItem>
                                        <SelectItem value="2">Martedì</SelectItem>
                                        <SelectItem value="3">Mercoledì</SelectItem>
                                        <SelectItem value="4">Giovedì</SelectItem>
                                        <SelectItem value="5">Venerdì</SelectItem>
                                        <SelectItem value="6">Sabato</SelectItem>
                                        <SelectItem value="0">Domenica</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label>Ora Inizio</Label>
                                <Input
                                    type="time"
                                    value={requestSlotData.start_time}
                                    onChange={(e) =>
                                        setRequestSlotData({
                                            ...requestSlotData,
                                            start_time: e.target.value,
                                        })
                                    }
                                    required
                                />
                            </div>
                            <div>
                                <Label>Ora Fine</Label>
                                <Input
                                    type="time"
                                    value={requestSlotData.end_time}
                                    onChange={(e) =>
                                        setRequestSlotData({
                                            ...requestSlotData,
                                            end_time: e.target.value,
                                        })
                                    }
                                    required
                                />
                            </div>
                            <Button type="submit">
                                <PlusCircle className="h-4 w-4 mr-2" />
                                Invia Richiesta Slot
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {/* Calendario */}
                <Card>
                    <CardHeader>
                        <CardTitle>Calendario (Slot + Appuntamenti)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Calendar
                            localizer={localizer}
                            events={calendarEvents}
                            startAccessor="start"
                            endAccessor="end"
                            view={clientCalendarView}
                            onView={(v) => setClientCalendarView(v)}
                            views={["month", "week", "day"]}
                            date={clientCalendarDate}
                            onNavigate={(d) => setClientCalendarDate(d)}
                            style={{ height: 600 }}
                            messages={{
                                next: "Successivo",
                                previous: "Precedente",
                                today: "Oggi",
                                month: "Mese",
                                week: "Settimana",
                                day: "Giorno",
                            }}
                             tooltipAccessor={(event) => {
                                if (event.isSlot) {
                                    return `Slot ${event.slotStatus} (Operatore: ${event.operator_name})`;
                                }
                                return `Appuntamento con Operatore: ${event.operatorName}`;
                            }}
                            eventPropGetter={(event) => {
                                if (event.isSlot) {
                                    if (event.slotStatus === "approved") {
                                        return { style: { backgroundColor: "#F59E0B" } };
                                    } else if (event.slotStatus === "pending") {
                                        return { style: { backgroundColor: "#9CA3AF" } };
                                    }
                                    return { style: { backgroundColor: "#6B7280" } };
                                }
                                let bg = "#3B82F6";
                                if (event.status === "completed") bg = "#10B981";
                                else if (event.status === "cancelled") bg = "#EF4444";
                                return { style: { backgroundColor: bg } };
                            }}
                            onSelectEvent={handleSelectClientEvent}
                        />
                    </CardContent>
                </Card>

                {error && (
                    <Alert variant="destructive" className="mt-4">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                {success && (
                    <Alert className="mt-4">
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}
            </div>
        );
    }

    /*******************************************
     * RENDER PRINCIPALE
     *******************************************/
    if (view === "login") return renderLogin();
    if (view === "register") return renderRegister();
    if (view === "recover") return renderRecover();

    if (user?.role === "admin") return renderAdmin();
    if (user?.role === "operator") return renderOperator();
    if (user?.role === "client") return renderClient();

    return null;
};

export default Dashboard;
