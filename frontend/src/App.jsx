import React, { useState } from 'react';
import axios from 'axios';
import { ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';

const CATEGORIES = [
  { id: 'grocery', label: 'Groceries', defaultVal: 6000 },
  { id: 'dining', label: 'Dining & restaurants', defaultVal: 3600 },
  { id: 'travel', label: 'Flights & hotels', defaultVal: 2400 },
  { id: 'gas', label: 'Gas & transit', defaultVal: 1800 },
  { id: 'streaming', label: 'Streaming & entertainment', defaultVal: 600 },
  { id: 'catch_all', label: 'General & other spending', defaultVal: 4800 },
];

const money = (n) => (n ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function App() {
  const [spending, setSpending] = useState(
    CATEGORIES.reduce((acc, cat) => ({ ...acc, [cat.id]: cat.defaultVal }), {})
  );
  const [mode, setMode] = useState('single'); // 'single' | 'wallet' | 'no-fee'
  const [includeBusiness, setIncludeBusiness] = useState(false);
  const [results, setResults] = useState([]);
  const [walletCombos, setWalletCombos] = useState([]);
  const [expandedCard, setExpandedCard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasCalculated, setHasCalculated] = useState(false);

  const handleInputChange = (category, value) => {
    setSpending((prev) => ({
      ...prev,
      [category]: Math.max(0, Number(value) || 0),
    }));
  };

  const calculateOptimizedCards = async () => {
    setLoading(true);
    try {
      const queryParam = `?include_business=${includeBusiness}`;
      if (mode === 'single') {
        const response = await axios.post(`https://spendwise-api-b5im.onrender.com/api/optimize${queryParam}`, spending);
        setResults(response.data);
      } else if (mode === 'wallet') {
        const response = await axios.post(`https://spendwise-api-b5im.onrender.com/api/optimize-wallets${queryParam}&top_n=3`, spending);
        setWalletCombos(response.data);
      } else if (mode === 'no-fee') {
        const response = await axios.post(`https://spendwise-api-b5im.onrender.com/api/optimize-no-fee${queryParam}`, spending);
        setResults(response.data);
      } else if (mode === 'student') {
        const response = await axios.post(`https://spendwise-api-b5im.onrender.com/api/optimize-student`, spending);
        setResults(response.data);
      }
      setHasCalculated(true);
    } catch (err) {
      console.error('Calculation failed:', err);
      alert('Could not reach the backend. The free Render instance may be waking up — try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  const totalAnnualSpend = Object.values(spending).reduce((sum, val) => sum + val, 0);

  const modeCopy = {
    single: { tab: 'Rank single cards', heading: 'Ranked cards', button: 'Rank my cards' },
    wallet: { tab: 'Best card pairs', heading: 'Best card pairs', button: 'Find best pairs' },
    'no-fee': { tab: 'No annual fee', heading: 'No annual fee cards', button: 'Find $0-fee cards' },
    student: { tab: 'For college students', heading: 'Cards for students', button: 'Find student cards' },
  };

  return (
    <div className="min-h-screen bg-[#EEF3EA] text-[#16231F] font-['IBM_Plex_Sans',_sans-serif]">
      <div className="max-w-5xl mx-auto px-6 md:px-10 py-10 md:py-14">

        {/* Masthead */}
        <header className="mb-10">
          <div className="flex items-baseline justify-between flex-wrap gap-2 border-b-2 border-[#16231F] pb-4">
            <h1 className="font-['Fraunces',_serif] text-4xl md:text-5xl font-normal tracking-tight">
              SpendWise
            </h1>
            <p className="text-sm text-[#4B5B54] max-w-xs text-right">
              A ledger for finding the credit card worth the most to you, dollar for dollar.
            </p>
          </div>

          {/* Mode selector — underline tabs, not pill buttons */}
          <nav className="flex gap-6 mt-5 border-b border-[#C7D2C4]">
            {Object.entries(modeCopy).map(([key, copy]) => (
              <button
                key={key}
                onClick={() => { setMode(key); setHasCalculated(false); }}
                className={`pb-3 text-sm font-medium transition-colors cursor-pointer border-b-2 -mb-px ${
                  mode === key
                    ? 'border-[#16231F] text-[#16231F]'
                    : 'border-transparent text-[#7C8A82] hover:text-[#16231F]'
                }`}
              >
                {copy.tab}
              </button>
            ))}
          </nav>

          <label className="flex items-center gap-2 text-sm text-[#4B5B54] mt-4 cursor-pointer select-none w-fit">
            <input
              type="checkbox"
              checked={includeBusiness}
              onChange={(e) => setIncludeBusiness(e.target.checked)}
              className="w-4 h-4 accent-[#16231F] cursor-pointer"
            />
            Include business cards
          </label>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-12 gap-10">

          {/* Spending worksheet */}
          <section className="lg:col-span-5">
            <h2 className="font-['Fraunces',_serif] text-xl mb-1">Your annual spending</h2>
            <p className="text-sm text-[#4B5B54] mb-5">Adjust each category to match your budget.</p>

            <div className="divide-y divide-[#C7D2C4]">
              {CATEGORIES.map((cat) => (
                <div key={cat.id} className="py-4 first:pt-0">
                  <div className="flex justify-between items-baseline mb-2">
                    <label htmlFor={cat.id} className="text-sm text-[#16231F]">{cat.label}</label>
                    <span className="font-['IBM_Plex_Mono',_monospace] text-sm tabular-nums">
                      ${money(spending[cat.id])}
                    </span>
                  </div>
                  <input
                    id={cat.id}
                    type="range"
                    min="0"
                    max="20000"
                    step="100"
                    value={spending[cat.id] || 0}
                    onChange={(e) => handleInputChange(cat.id, e.target.value)}
                    className="w-full h-[2px] bg-[#7C9985] rounded-none appearance-none cursor-pointer accent-[#16231F]
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                      [&::-webkit-slider-thumb]:bg-[#16231F] [&::-webkit-slider-thumb]:rounded-none [&::-webkit-slider-thumb]:cursor-pointer
                      [&::-moz-range-thumb]:appearance-none [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3
                      [&::-moz-range-thumb]:bg-[#16231F] [&::-moz-range-thumb]:rounded-none [&::-moz-range-thumb]:border-none [&::-moz-range-thumb]:cursor-pointer"
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-between items-baseline border-t-2 border-[#16231F] mt-2 pt-3">
              <span className="text-sm font-medium">Total annual spend</span>
              <span className="font-['IBM_Plex_Mono',_monospace] text-base tabular-nums font-medium">
                ${money(totalAnnualSpend)}
              </span>
            </div>

            <button
              onClick={calculateOptimizedCards}
              disabled={loading}
              className="w-full mt-6 py-3 px-4 bg-[#16231F] hover:bg-[#0D1512] text-[#EEF3EA] text-sm font-medium
                transition-colors cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? 'Calculating…' : modeCopy[mode].button}
              {!loading && <ArrowRight className="w-3.5 h-3.5" />}
            </button>
          </section>

          {/* Results */}
          <section className="lg:col-span-7">
            <h2 className="font-['Fraunces',_serif] text-xl mb-1">{modeCopy[mode].heading}</h2>
            <p className="text-sm text-[#4B5B54] mb-1">
              {mode === 'wallet'
                ? 'Two-card combinations ranked by combined first-year value.'
                : mode === 'student'
                ? 'Cards built for no or limited credit history, ranked by first-year value.'
                : 'Ranked by projected net value in the first year.'}
            </p>
            {mode === 'student' && (
              <p className="text-xs text-[#7C8A82] mb-5 max-w-md">
                This list covers cards designed to approve people with no credit history at all.
                Plenty of students also get approved for other cards on this list depending on
                their individual credit file — this section isn't the only option, just the
                surest bet if you're starting from zero.
              </p>
            )}
            {mode !== 'student' && <div className="mb-5" />}

            {!hasCalculated ? (
              <div className="border border-dashed border-[#B7C4B2] py-16 text-center text-[#7C8A82]">
                <p className="text-sm">Set your spending, then calculate to see results here.</p>
              </div>
            ) : mode === 'wallet' ? (
              <div>
                {walletCombos.map((wallet, comboIdx) => (
                  <div key={comboIdx} className="border-t border-[#C7D2C4] py-5 first:border-t-0 first:pt-0">
                    <div className="flex justify-between items-start gap-4 mb-3">
                      <div>
                        <span className="font-['Fraunces',_serif] text-2xl text-[#7C8A82] mr-2">
                          {comboIdx + 1}
                        </span>
                        <span className="text-base font-medium">
                          {wallet.cards.map((c) => c.card_name).join(' + ')}
                        </span>
                      </div>
                      <span className="font-['IBM_Plex_Mono',_monospace] text-lg tabular-nums font-medium whitespace-nowrap">
                        ${money(wallet.total_net_value)}
                      </span>
                    </div>

                    <div className="flex gap-6 text-xs text-[#4B5B54] mb-3 pl-9">
                      <span>Rewards <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#16231F]">${money(wallet.total_annual_rewards)}</span></span>
                      <span>Bonus <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#8A6D3B]">+${money(wallet.total_signup_bonus)}</span></span>
                      <span>Fees <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#A23B2E]">-${money(wallet.total_effective_fee)}</span></span>
                    </div>

                    <div className="pl-9 space-y-1">
                      {wallet.cards.map((card, idx) => (
                        <div key={card.card_id} className="flex justify-between text-sm text-[#4B5B54]">
                          <span>{card.card_name}</span>
                          <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums">${money(card.net_first_year_value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div>
                {results.map((card, idx) => {
                  const isExpanded = expandedCard === card.card_name;
                  return (
                    <div
                      key={card.card_name}
                      className={`border-t border-[#C7D2C4] py-5 first:border-t-0 first:pt-0 ${
                        idx === 0 ? 'border-l-2 border-l-[#8A6D3B] pl-4 -ml-4' : ''
                      }`}
                    >
                      <div className="flex justify-between items-start gap-4 mb-3">
                        <div className="flex items-baseline gap-3">
                          <span className="font-['Fraunces',_serif] text-2xl text-[#7C8A82]">{idx + 1}</span>
                          <span className="text-base font-medium">{card.card_name}</span>
                        </div>
                        <span className="font-['IBM_Plex_Mono',_monospace] text-lg tabular-nums font-medium whitespace-nowrap">
                          ${money(card.net_first_year_value)}
                        </span>
                      </div>

                      <div className="flex gap-6 text-xs text-[#4B5B54] pl-9 mb-2">
                        <span>Rewards <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#16231F]">${money(card.annual_rewards)}</span></span>
                        <span>Bonus <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#8A6D3B]">
                          {card.signup_bonus_earned > 0 ? `+$${money(card.signup_bonus_earned)}` : '$0.00'}
                        </span></span>
                        <span>Fee <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums text-[#A23B2E]">-${money(card.effective_annual_fee)}</span></span>
                      </div>

                      <button
                        onClick={() => setExpandedCard(isExpanded ? null : card.card_name)}
                        className="flex items-center gap-1 text-xs text-[#7C8A82] hover:text-[#16231F] pl-9 cursor-pointer"
                      >
                        {isExpanded ? 'Hide category breakdown' : 'See category breakdown'}
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>

                      {isExpanded && card.breakdown && (
                        <div className="pl-9 mt-3 grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-1.5 text-xs">
                          {Object.entries(card.breakdown).map(([category, amount]) => (
                            <div key={category} className="flex justify-between border-b border-dotted border-[#C7D2C4] pb-1">
                              <span className="text-[#4B5B54]">{category.replace('_', ' ')}</span>
                              <span className="font-['IBM_Plex_Mono',_monospace] tabular-nums">${money(amount)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}