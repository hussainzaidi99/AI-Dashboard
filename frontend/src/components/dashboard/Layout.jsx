import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import LightRays from '../backgrounds/LightRays';

const Layout = ({ children }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <div className="flex h-screen w-screen bg-[#000000] text-foreground overflow-hidden font-sans selection:bg-white/20">
            {/* Background Effect - Enhanced Silver Glow */}
            <div className="fixed inset-0 z-0 opacity-85">
                <LightRays
                    raysOrigin="top-center"
                    raysColor="#f8fafc"
                    raysSpeed={0.4}
                    lightSpread={0.8}
                    rayLength={2.2}
                    followMouse={true}
                    mouseInfluence={0.03}
                    pulsating={true}
                />
            </div>

            {/* Sidebar */}
            <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />

            {/* Main Content Area */}
            <main className={`flex-1 flex flex-col relative z-10 overflow-hidden transition-all duration-300 ${isCollapsed ? 'pl-0' : ''}`}>
                <Navbar />

                <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 lg:p-10 custom-scrollbar">
                    <div className="max-w-[1600px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Layout;
