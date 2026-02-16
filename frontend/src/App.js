import React, { useState, useEffect, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Zap, MessageCircle, X, Send, Phone, MapPin, Wrench, Star, Clock, Shield, ChevronRight, Users, BarChart3, CheckCircle, AlertCircle, Loader2, Mail, Eye, FileText } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate unique session ID
const generateSessionId = () => {
  return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
};

// ============== CHATBOT WIDGET ==============
const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "G'day! 👋 Welcome to Add Power Electrics - your trusted local sparky in Clyde North with a 5-star rating! How can I help you today?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(generateSessionId);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: inputValue,
        session_id: sessionId
      });

      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          type: 'bot',
          text: response.data.response,
          timestamp: new Date()
        }]);
      }, 800);
    } catch (error) {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        type: 'bot',
        text: "Sorry, I'm having trouble connecting. Please call us at 0448 195 614 for immediate assistance!",
        timestamp: new Date()
      }]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickReplies = [
    "Get a free quote",
    "What areas do you service?",
    "Emergency electrical help"
  ];

  return (
    <>
      {/* Chat Toggle Button */}
      {!isOpen && (
        <button
          data-testid="chat-toggle-btn"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-24 right-6 w-16 h-16 bg-[#2563EB] hover:bg-[#1d4ed8] text-white rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 hover:scale-105 animate-pulse-glow z-[9999]"
        >
          <MessageCircle size={28} />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div 
          data-testid="chat-window"
          className="fixed bottom-24 right-6 w-[380px] h-[550px] bg-zinc-950 border border-zinc-800 rounded-lg shadow-2xl overflow-hidden flex flex-col z-[9999] animate-slide-up"
        >
          {/* Header */}
          <div className="bg-[#2563EB] p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Zap size={24} className="text-[#FACC15]" />
              </div>
              <div>
                <h3 className="font-bold text-white uppercase tracking-wide text-sm" style={{fontFamily: 'Barlow Condensed'}}>
                  Add Power Electrics
                </h3>
                <p className="text-white/80 text-xs flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                  Online now
                </p>
              </div>
            </div>
            <button
              data-testid="chat-close-btn"
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 bg-zinc-900/50 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  data-testid={`chat-message-${idx}`}
                  className={`max-w-[85%] p-3 text-sm ${
                    msg.type === 'user'
                      ? 'bg-[#2563EB] text-white chat-bubble-user'
                      : 'bg-zinc-800 text-zinc-100 chat-bubble-bot border-l-2 border-[#FACC15]'
                  }`}
                  style={{ whiteSpace: 'pre-wrap' }}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-zinc-800 text-zinc-100 chat-bubble-bot border-l-2 border-[#FACC15] p-3 flex gap-1">
                  <span className="w-2 h-2 bg-zinc-400 rounded-full typing-dot"></span>
                  <span className="w-2 h-2 bg-zinc-400 rounded-full typing-dot"></span>
                  <span className="w-2 h-2 bg-zinc-400 rounded-full typing-dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Replies */}
          {messages.length <= 2 && (
            <div className="px-4 py-2 bg-zinc-900 border-t border-zinc-800 flex gap-2 overflow-x-auto">
              {quickReplies.map((reply, idx) => (
                <button
                  key={idx}
                  data-testid={`quick-reply-${idx}`}
                  onClick={() => {
                    setInputValue(reply);
                    setTimeout(() => {
                      const input = document.querySelector('[data-testid="chat-input"]');
                      if (input) input.focus();
                    }, 100);
                  }}
                  className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs rounded-full whitespace-nowrap transition-colors border border-zinc-700"
                >
                  {reply}
                </button>
              ))}
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-zinc-950 border-t border-zinc-800">
            <div className="flex gap-2">
              <input
                data-testid="chat-input"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded-sm px-4 py-3 text-white text-sm focus:border-[#2563EB] transition-colors placeholder:text-zinc-500"
              />
              <button
                data-testid="chat-send-btn"
                onClick={sendMessage}
                disabled={!inputValue.trim()}
                className="bg-[#2563EB] hover:bg-[#1d4ed8] disabled:bg-zinc-700 disabled:cursor-not-allowed text-white px-4 rounded-sm transition-colors btn-press"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ============== LANDING PAGE ==============
const LandingPage = () => {
  const navigate = useNavigate();

  const services = [
    { icon: <Zap size={24} />, title: "Powerpoints", desc: "Installation & repairs" },
    { icon: <Shield size={24} />, title: "Safety Switches", desc: "RCD & switchboards" },
    { icon: <Wrench size={24} />, title: "Repairs", desc: "Fault finding & fixes" },
  ];

  const reviews = [
    { name: "Hyungchul Lee", text: "Did a great job, his pricing is fair. Professional, gives great advice. Definitely recommend." },
    { name: "Myles Angelo", text: "Very reliable and gets the job done with quality and eye to detail. Highly recommend." },
    { name: "Beau Gielen", text: "Attention to detail and professionalism is the best. Get in contact for any Electrical work needed." },
  ];

  return (
    <div className="min-h-screen bg-[#FAFAFA] relative overflow-hidden">
      {/* Grid Pattern Background */}
      <div className="fixed inset-0 grid-pattern pointer-events-none"></div>
      
      {/* Hero Section */}
      <section className="relative py-8 md:py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Header */}
          <header className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-[#2563EB] rounded-sm flex items-center justify-center">
                <Zap size={28} className="text-[#FACC15]" />
              </div>
              <div>
                <h1 className="text-xl font-bold uppercase tracking-tight text-zinc-900" style={{fontFamily: 'Barlow Condensed'}}>
                  Add Power Electrics
                </h1>
                <p className="text-xs text-zinc-500 font-mono">CLYDE NORTH & SURROUNDS</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <a 
                href="tel:0448195614"
                data-testid="header-phone-btn"
                className="hidden md:flex items-center gap-2 text-zinc-700 hover:text-[#2563EB] transition-colors"
              >
                <Phone size={18} />
                <span className="font-semibold">0448 195 614</span>
              </a>
              <button
                data-testid="admin-dashboard-btn"
                onClick={() => navigate('/admin')}
                className="px-4 py-2 bg-zinc-900 text-white text-sm font-bold uppercase tracking-wider rounded-sm hover:bg-zinc-800 transition-colors"
                style={{fontFamily: 'Barlow Condensed'}}
              >
                Admin
              </button>
            </div>
          </header>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6">
            {/* Main Hero Card */}
            <div className="md:col-span-8 bg-zinc-900 rounded-sm p-8 md:p-12 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-[#2563EB]/20 to-transparent"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} size={16} className="text-[#FACC15] fill-[#FACC15]" />
                    ))}
                  </div>
                  <span className="text-white/80 text-sm font-mono">5.0 (37 reviews)</span>
                </div>
                <h2 className="text-4xl md:text-6xl font-bold text-white uppercase tracking-tight leading-none mb-4" style={{fontFamily: 'Barlow Condensed'}}>
                  Your Local<br />
                  <span className="text-[#FACC15]">Trusted Sparky</span>
                </h2>
                <p className="text-white/70 text-lg mb-8 max-w-lg">
                  Professional electrical services for homes and businesses in Melbourne's south-east. Licensed, insured, and ready to help.
                </p>
                <div className="flex flex-wrap gap-4">
                  <a 
                    href="tel:0448195614"
                    data-testid="hero-call-btn"
                    className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1d4ed8] text-white font-bold uppercase tracking-wider px-8 py-4 rounded-sm transition-all btn-press"
                    style={{fontFamily: 'Barlow Condensed'}}
                  >
                    <Phone size={20} />
                    Call Now
                  </a>
                  <button
                    data-testid="hero-chat-btn"
                    onClick={() => document.querySelector('[data-testid="chat-toggle-btn"]')?.click()}
                    className="inline-flex items-center gap-2 bg-[#FACC15] hover:bg-[#eab308] text-black font-bold uppercase tracking-wider px-8 py-4 rounded-sm transition-all btn-press"
                    style={{fontFamily: 'Barlow Condensed'}}
                  >
                    <MessageCircle size={20} />
                    Chat with us
                  </button>
                </div>
              </div>
            </div>

            {/* Stats Card */}
            <div className="md:col-span-4 bg-white border border-zinc-200 rounded-sm p-6 flex flex-col justify-between">
              <div>
                <p className="text-xs font-mono uppercase text-zinc-400 mb-2">Service Stats</p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                    <span className="text-zinc-600">Response Time</span>
                    <span className="font-bold text-zinc-900">Same Day</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                    <span className="text-zinc-600">Service Area</span>
                    <span className="font-bold text-zinc-900">40km+</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-600">Happy Customers</span>
                    <span className="font-bold text-zinc-900">500+</span>
                  </div>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-zinc-100">
                <div className="flex items-center gap-2 text-[#2563EB]">
                  <Clock size={18} />
                  <span className="text-sm font-medium">Open 9 AM - 5 PM</span>
                </div>
              </div>
            </div>

            {/* Services Cards */}
            {services.map((service, idx) => (
              <div 
                key={idx}
                className="md:col-span-4 bg-white border border-zinc-200 rounded-sm p-6 hover:border-[#2563EB]/30 transition-colors group"
              >
                <div className="w-12 h-12 bg-[#2563EB]/10 rounded-sm flex items-center justify-center text-[#2563EB] mb-4 group-hover:bg-[#2563EB] group-hover:text-white transition-colors">
                  {service.icon}
                </div>
                <h3 className="text-xl font-bold uppercase tracking-tight text-zinc-900 mb-1" style={{fontFamily: 'Barlow Condensed'}}>
                  {service.title}
                </h3>
                <p className="text-zinc-500 text-sm">{service.desc}</p>
              </div>
            ))}

            {/* Location Card */}
            <div className="md:col-span-6 bg-[#2563EB] rounded-sm p-6 text-white">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-sm flex items-center justify-center flex-shrink-0">
                  <MapPin size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold uppercase tracking-tight mb-2" style={{fontFamily: 'Barlow Condensed'}}>
                    Service Areas
                  </h3>
                  <p className="text-white/80 text-sm leading-relaxed">
                    Clyde North, Cranbourne, Berwick, Narre Warren, Pakenham, Officer, Hallam, Dandenong, and all surrounding suburbs in Melbourne's south-east.
                  </p>
                </div>
              </div>
            </div>

            {/* CTA Card */}
            <div className="md:col-span-6 bg-[#FACC15] rounded-sm p-6 text-black">
              <div className="flex items-center justify-between h-full">
                <div>
                  <h3 className="text-xl font-bold uppercase tracking-tight mb-1" style={{fontFamily: 'Barlow Condensed'}}>
                    Free Quotes Available
                  </h3>
                  <p className="text-black/70 text-sm">No obligation, honest pricing</p>
                </div>
                <ChevronRight size={32} className="text-black/50" />
              </div>
            </div>
          </div>

          {/* Reviews Section */}
          <div className="mt-12">
            <h3 className="text-2xl font-bold uppercase tracking-tight text-zinc-900 mb-6" style={{fontFamily: 'Barlow Condensed'}}>
              What Our Customers Say
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {reviews.map((review, idx) => (
                <div 
                  key={idx}
                  data-testid={`review-card-${idx}`}
                  className="bg-white border border-zinc-200 rounded-sm p-6"
                >
                  <div className="flex mb-3">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} size={14} className="text-[#FACC15] fill-[#FACC15]" />
                    ))}
                  </div>
                  <p className="text-zinc-600 text-sm mb-4 leading-relaxed">"{review.text}"</p>
                  <p className="font-semibold text-zinc-900 text-sm">{review.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-zinc-900 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Zap size={24} className="text-[#FACC15]" />
              <span className="font-bold uppercase tracking-tight" style={{fontFamily: 'Barlow Condensed'}}>
                Add Power Electrics
              </span>
            </div>
            <div className="flex items-center gap-6 text-zinc-400 text-sm">
              <span>Licensed & Insured</span>
              <span>•</span>
              <a href="tel:0448195614" className="hover:text-white transition-colors">0448 195 614</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Chatbot Widget */}
      <ChatbotWidget />
    </div>
  );
};

// ============== ADMIN DASHBOARD ==============
const AdminDashboard = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState({ total_leads: 0, new_leads: 0, contacted: 0, booked: 0, completed: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [emailPreview, setEmailPreview] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [leadsRes, statsRes] = await Promise.all([
        axios.get(`${API}/leads`),
        axios.get(`${API}/stats`)
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (leadId, newStatus) => {
    try {
      await axios.patch(`${API}/leads/${leadId}/status?status=${newStatus}`);
      fetchData();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const sendSmsNotification = async (leadId) => {
    try {
      const response = await axios.post(`${API}/sms/send?lead_id=${leadId}`);
      alert(response.data.message);
      fetchData();
    } catch (error) {
      console.error('Failed to send SMS:', error);
    }
  };

  const sendQuoteEmail = async (leadId) => {
    try {
      const response = await axios.post(`${API}/email/send-quote?lead_id=${leadId}`);
      alert('Quote email sent successfully! (Simulated)');
      fetchData();
    } catch (error) {
      console.error('Failed to send quote email:', error);
    }
  };

  const previewEmail = async (leadId, type) => {
    try {
      const response = await axios.get(`${API}/email/preview/${leadId}`);
      setEmailPreview({ ...response.data[type], type, leadId });
      setShowEmailModal(true);
    } catch (error) {
      console.error('Failed to preview email:', error);
    }
  };

  const statusColors = {
    new: 'bg-blue-100 text-blue-800',
    contacted: 'bg-yellow-100 text-yellow-800',
    booked: 'bg-green-100 text-green-800',
    completed: 'bg-zinc-100 text-zinc-800'
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-AU', { 
      day: 'numeric', 
      month: 'short', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <header className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#2563EB] rounded-sm flex items-center justify-center">
              <Zap size={24} className="text-[#FACC15]" />
            </div>
            <div>
              <h1 className="text-lg font-bold uppercase tracking-tight" style={{fontFamily: 'Barlow Condensed'}}>
                Lead Dashboard
              </h1>
              <p className="text-xs text-zinc-500 font-mono">ADD POWER ELECTRICS</p>
            </div>
          </div>
          <button
            data-testid="back-to-site-btn"
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-bold uppercase tracking-wider rounded-sm transition-colors"
            style={{fontFamily: 'Barlow Condensed'}}
          >
            Back to Site
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4">
            <p className="text-xs font-mono uppercase text-zinc-500 mb-1">Total Leads</p>
            <p className="text-3xl font-bold text-white" data-testid="stat-total">{stats.total_leads}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4">
            <p className="text-xs font-mono uppercase text-zinc-500 mb-1">New</p>
            <p className="text-3xl font-bold text-blue-400" data-testid="stat-new">{stats.new_leads}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4">
            <p className="text-xs font-mono uppercase text-zinc-500 mb-1">Contacted</p>
            <p className="text-3xl font-bold text-yellow-400" data-testid="stat-contacted">{stats.contacted}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4">
            <p className="text-xs font-mono uppercase text-zinc-500 mb-1">Booked</p>
            <p className="text-3xl font-bold text-green-400" data-testid="stat-booked">{stats.booked}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4">
            <p className="text-xs font-mono uppercase text-zinc-500 mb-1">Completed</p>
            <p className="text-3xl font-bold text-zinc-400" data-testid="stat-completed">{stats.completed}</p>
          </div>
        </div>

        {/* Leads Table */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
            <h2 className="text-lg font-bold uppercase tracking-tight" style={{fontFamily: 'Barlow Condensed'}}>
              Recent Leads
            </h2>
            <button
              data-testid="refresh-leads-btn"
              onClick={fetchData}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              <BarChart3 size={20} />
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-[#2563EB] mx-auto" />
              <p className="text-zinc-500 mt-2">Loading leads...</p>
            </div>
          ) : leads.length === 0 ? (
            <div className="p-12 text-center">
              <Users size={48} className="text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">No leads yet. Start a chat on the website to capture leads!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Name</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Phone</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Suburb</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Job</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Date</th>
                    <th className="text-left px-6 py-3 text-xs font-mono uppercase text-zinc-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead, idx) => (
                    <tr 
                      key={lead.id}
                      data-testid={`lead-row-${idx}`}
                      className="border-t border-zinc-800 hover:bg-zinc-800/30 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium">{lead.name}</td>
                      <td className="px-6 py-4">
                        <a href={`tel:${lead.phone}`} className="text-[#2563EB] hover:underline">
                          {lead.phone}
                        </a>
                      </td>
                      <td className="px-6 py-4 text-zinc-400">{lead.suburb}</td>
                      <td className="px-6 py-4 text-zinc-400 max-w-[200px] truncate">{lead.job_description}</td>
                      <td className="px-6 py-4">
                        <select
                          data-testid={`status-select-${idx}`}
                          value={lead.status}
                          onChange={(e) => updateStatus(lead.id, e.target.value)}
                          className={`px-2 py-1 rounded text-xs font-medium ${statusColors[lead.status]} border-0 cursor-pointer`}
                        >
                          <option value="new">New</option>
                          <option value="contacted">Contacted</option>
                          <option value="booked">Booked</option>
                          <option value="completed">Completed</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 text-zinc-500 text-sm">{formatDate(lead.created_at)}</td>
                      <td className="px-6 py-4">
                        <button
                          data-testid={`sms-btn-${idx}`}
                          onClick={() => sendSmsNotification(lead.id)}
                          className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                            lead.sms_sent 
                              ? 'bg-green-900/30 text-green-400 cursor-default' 
                              : 'bg-[#2563EB] hover:bg-[#1d4ed8] text-white'
                          }`}
                          disabled={lead.sms_sent}
                        >
                          {lead.sms_sent ? (
                            <span className="flex items-center gap-1">
                              <CheckCircle size={12} /> SMS Sent
                            </span>
                          ) : (
                            'Send SMS'
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* SMS Integration Notice */}
        <div className="mt-6 bg-zinc-900 border border-zinc-800 rounded-sm p-4 flex items-start gap-3">
          <AlertCircle size={20} className="text-[#FACC15] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-zinc-300">
              <strong>SMS Notifications:</strong> Currently simulated. To enable real SMS notifications to <span className="font-mono text-[#FACC15]">0448 195 614</span>, add your Twilio credentials to the backend configuration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============== MAIN APP ==============
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
