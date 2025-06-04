#!/usr/bin/env python3
"""
Domain Mapper - Créé une cartographie visuelle des domaines découverts
Usage: python3 domain_mapper.py <fichier_amass.txt>
"""

import sys
import re
import os
from typing import Set, Dict, List, Tuple
from collections import defaultdict
import hashlib

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

class DomainMapper:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.domains: Set[str] = set()
        self.relations: List[Tuple[str, str, str]] = []
        self.ips: Set[str] = set()
        self.organizations: Set[str] = set()
        self.root_domain = ""
        
    def _safe_node_id(self, node_name: str) -> str:
        """Créé un ID sûr pour Graphviz en remplaçant les caractères problématiques"""
        # Remplacer les caractères problématiques par des underscores
        safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_name)
        # S'assurer que l'ID commence par une lettre
        if safe_id[0].isdigit():
            safe_id = 'n_' + safe_id
        return safe_id
        
    def parse_amass_file(self):
        """Parse le fichier Amass et extrait toutes les relations"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Pattern: SOURCE (TYPE) --> RELATION --> TARGET (TYPE)
                    pattern = r'^(.+?) \((.+?)\) --> (.+?) --> (.+?) \((.+?)\)$'
                    match = re.match(pattern, line)
                    
                    if match:
                        source, source_type, relation, target, target_type = match.groups()
                        source = source.strip()
                        target = target.strip()
                        relation = relation.strip()
                        
                        # Collecter les éléments
                        if source_type == 'FQDN':
                            self.domains.add(source)
                            # Trouver le domaine racine (hydrogeotechnique.com)
                            if source == 'hydrogeotechnique.com':
                                self.root_domain = source
                        
                        if target_type == 'FQDN':
                            self.domains.add(target)
                        elif target_type == 'IPAddress':
                            self.ips.add(target)
                        elif target_type == 'RIROrganization':
                            self.organizations.add(target)
                        
                        # Stocker la relation
                        self.relations.append((source, relation, target))
                        
        except FileNotFoundError:
            print(f"❌ Erreur: Fichier '{self.filepath}' non trouvé")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier: {e}")
            sys.exit(1)
    
    def create_graphviz_map(self, output_format='svg', show_ips=True, show_orgs=False):
        """Créé une cartographie avec Graphviz"""
        if not HAS_GRAPHVIZ:
            print("❌ Graphviz non installé. Installez-le avec: pip install graphviz")
            return
        
        # Créer le graphe
        dot = graphviz.Digraph(comment=f'Cartographie de {self.root_domain}')
        dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='1.0')
        dot.attr('node', style='filled', fontname='Arial')
        dot.attr('edge', fontname='Arial', fontsize='10')
        
        # Styles pour différents types de nœuds
        domain_style = {'fillcolor': '#e1f5fe', 'shape': 'box', 'fontcolor': '#01579b'}
        subdomain_style = {'fillcolor': '#f3e5f5', 'shape': 'ellipse', 'fontcolor': '#4a148c'}
        ip_style = {'fillcolor': '#fff3e0', 'shape': 'diamond', 'fontcolor': '#e65100'}
        external_style = {'fillcolor': '#fce4ec', 'shape': 'box', 'fontcolor': '#880e4f'}
        org_style = {'fillcolor': '#e8f5e8', 'shape': 'house', 'fontcolor': '#1b5e20'}
        
        # Mappage des noms vers des IDs sûrs
        node_mapping = {}
        
        # Ajouter le domaine principal
        if self.root_domain:
            safe_id = self._safe_node_id(self.root_domain)
            node_mapping[self.root_domain] = safe_id
            dot.node(safe_id, self.root_domain, **domain_style, 
                    style='filled,bold', penwidth='3')
        
        # Ajouter les sous-domaines
        for domain in self.domains:
            if domain != self.root_domain:
                safe_id = self._safe_node_id(domain)
                node_mapping[domain] = safe_id
                
                if self.root_domain and self.root_domain in domain:
                    # Sous-domaine - raccourcir le label
                    short_label = domain.replace(f'.{self.root_domain}', '')
                    if len(short_label) > 20:
                        short_label = short_label[:17] + '...'
                    dot.node(safe_id, short_label, **subdomain_style)
                else:
                    # Domaine externe - raccourcir si nécessaire
                    display_name = domain
                    if len(display_name) > 25:
                        display_name = display_name[:22] + '...'
                    dot.node(safe_id, display_name, **external_style)
        
        # Ajouter les IPs si demandé
        if show_ips:
            for ip in self.ips:
                safe_id = self._safe_node_id(ip)
                node_mapping[ip] = safe_id
                
                # Simplifier l'affichage des IPv6
                if ':' in ip and len(ip) > 20:
                    label = ip[:15] + '...'
                else:
                    label = ip
                dot.node(safe_id, label, **ip_style)
        
        # Ajouter les organisations si demandé
        if show_orgs:
            for org in self.organizations:
                safe_id = self._safe_node_id(org)
                node_mapping[org] = safe_id
                # Raccourcir les noms d'organisations
                display_name = org
                if len(display_name) > 15:
                    display_name = display_name[:12] + '...'
                dot.node(safe_id, display_name, **org_style)
        
        # Ajouter les relations importantes seulement
        relation_colors = {
            'node': '#2196f3',           # Bleu pour sous-domaines
            'a_record': '#4caf50',       # Vert pour résolution A
            'aaaa_record': '#8bc34a',    # Vert clair pour IPv6
            'cname_record': '#ff9800',   # Orange pour CNAME
            'mx_record': '#f44336',      # Rouge pour mail
            'ns_record': '#9c27b0',      # Violet pour DNS
        }
        
        # Filtrer les relations importantes
        important_relations = ['node', 'a_record', 'cname_record', 'mx_record', 'ns_record']
        
        for source, relation, target in self.relations:
            # Ne garder que les relations importantes
            if relation not in important_relations:
                continue
                
            # Filtrer selon les options
            if not show_ips and target in self.ips:
                continue
            if not show_orgs and target in self.organizations:
                continue
            
            # Vérifier que les nœuds existent
            if source not in node_mapping or target not in node_mapping:
                continue
            
            color = relation_colors.get(relation, '#666666')
            
            # Styles spéciaux pour certaines relations
            if relation == 'node':
                dot.edge(node_mapping[source], node_mapping[target], 
                        color=color, penwidth='2')
            elif relation in ['a_record', 'aaaa_record']:
                dot.edge(node_mapping[source], node_mapping[target], 
                        label='IP', color=color, style='dashed')
            elif relation == 'cname_record':
                dot.edge(node_mapping[source], node_mapping[target], 
                        label='CNAME', color=color, style='dotted')
            elif relation == 'mx_record':
                dot.edge(node_mapping[source], node_mapping[target], 
                        label='MAIL', color=color)
            elif relation == 'ns_record':
                dot.edge(node_mapping[source], node_mapping[target], 
                        label='DNS', color=color)
        
        # Générer le fichier
        output_file = f"domain_map_{self.root_domain.replace('.', '_')}"
        
        try:
            dot.render(output_file, format=output_format, cleanup=True)
            print(f"✅ Cartographie générée: {output_file}.{output_format}")
            
            # Afficher quelques statistiques
            print(f"\n📊 Statistiques de la cartographie:")
            print(f"  🌐 Domaines: {len(self.domains)}")
            print(f"  📍 Adresses IP: {len(self.ips)}")
            print(f"  🔗 Relations importantes: {len([r for r in self.relations if r[1] in important_relations])}")
            print(f"  🏢 Organisations: {len(self.organizations)}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
    
    def create_simple_text_map(self):
        """Créé une cartographie textuelle simple"""
        print(f"\n🗺️  CARTOGRAPHIE DE {self.root_domain.upper()}")
        print("=" * 60)
        
        # Organiser les sous-domaines par fonction
        subdomains = [d for d in self.domains if self.root_domain in d and d != self.root_domain]
        external_domains = [d for d in self.domains if self.root_domain not in d]
        
        print(f"\n🏠 DOMAINE PRINCIPAL")
        print(f"├── {self.root_domain}")
        
        # IPs du domaine principal
        main_ips = []
        for source, relation, target in self.relations:
            if source == self.root_domain and relation in ['a_record', 'aaaa_record']:
                main_ips.append(target)
        
        for ip in main_ips:
            print(f"│   └── 📍 {ip}")
        
        print(f"\n🌿 SOUS-DOMAINES ({len(subdomains)})")
        for subdomain in sorted(subdomains):
            # Trouver les IPs de ce sous-domaine
            subdomain_ips = []
            for source, relation, target in self.relations:
                if source == subdomain and relation in ['a_record', 'aaaa_record']:
                    subdomain_ips.append(target)
                elif source == subdomain and relation == 'cname_record':
                    subdomain_ips.append(f"→ {target}")
            
            print(f"├── {subdomain}")
            for ip in subdomain_ips[:2]:  # Limiter à 2 IPs
                print(f"│   └── 📍 {ip}")
        
        if external_domains:
            print(f"\n🌐 DOMAINES EXTERNES ({len(external_domains)})")
            for domain in sorted(external_domains)[:10]:  # Limiter à 10
                print(f"├── {domain}")
        
        # Statistiques réseau
        unique_ips = len(self.ips)
        print(f"\n📊 RÉSUMÉ")
        print(f"├── Sous-domaines: {len(subdomains)}")
        print(f"├── Domaines externes: {len(external_domains)}")
        print(f"├── Adresses IP uniques: {unique_ips}")
        print(f"└── Relations totales: {len(self.relations)}")
    
    def create_html_map(self):
        """Créé une cartographie interactive en HTML avec une belle UI"""
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🗺️ Cartographie de {domain}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .header h1 {{
            font-size: 2.2em;
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .controls {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .control-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .btn.active {{
            background: linear-gradient(135deg, #f093fb, #f5576c);
        }}
        
        .network-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            height: 70vh;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            position: relative;
        }}
        
        #network {{
            width: 100%;
            height: 100%;
            border-radius: 10px;
        }}
        
        .legend {{
            position: absolute;
            top: 30px;
            right: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .legend h3 {{
            margin-bottom: 10px;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            font-size: 0.9em;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid #fff;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }}
        
        .info-panel {{
            position: absolute;
            bottom: 30px;
            left: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            max-width: 300px;
            display: none;
        }}
        
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #667eea;
        }}
        
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .toast {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2ecc71;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }}
        
        .toast.show {{
            transform: translateX(0);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .control-group {{
                justify-content: center;
            }}
            
            .legend, .info-panel {{
                position: relative;
                margin-bottom: 20px;
            }}
            
            .network-container {{
                height: 60vh;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-map-marked-alt"></i>
                Cartographie de {domain}
            </h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{domain_count}</div>
                    <div class="stat-label"><i class="fas fa-globe"></i> Domaines</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{subdomain_count}</div>
                    <div class="stat-label"><i class="fas fa-sitemap"></i> Sous-domaines</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{ip_count}</div>
                    <div class="stat-label"><i class="fas fa-server"></i> Adresses IP</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{relation_count}</div>
                    <div class="stat-label"><i class="fas fa-link"></i> Relations</div>
                </div>
            </div>
        </div>

        <div class="controls">
            <div class="control-group">
                <button class="btn active" onclick="togglePhysics()">
                    <i class="fas fa-magic"></i> Physique
                </button>
                <button class="btn" onclick="resetView()">
                    <i class="fas fa-home"></i> Centrer
                </button>
                <button class="btn" onclick="toggleIPs()">
                    <i class="fas fa-server"></i> Afficher IPs
                </button>
                <button class="btn" onclick="exportImage()">
                    <i class="fas fa-download"></i> Exporter PNG
                </button>
                <button class="btn" onclick="toggleFullscreen()">
                    <i class="fas fa-expand"></i> Plein écran
                </button>
            </div>
        </div>

        <div class="network-container">
            <div class="loading">
                <div class="spinner"></div>
                <div>Génération de la cartographie...</div>
            </div>
            
            <div class="legend">
                <h3><i class="fas fa-info-circle"></i> Légende</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e1f5fe;"></div>
                    <span>Domaine principal</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f3e5f5;"></div>
                    <span>Sous-domaines</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #fff3e0;"></div>
                    <span>Adresses IP</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #fce4ec;"></div>
                    <span>Services externes</span>
                </div>
            </div>
            
            <div class="info-panel" id="infoPanel">
                <h4>Informations du nœud</h4>
                <div id="nodeInfo"></div>
            </div>
            
            <div id="network"></div>
        </div>
    </div>

    <script>
        let network;
        let nodes;
        let edges;
        let physicsEnabled = true;
        let showIPs = true;
        
        // Données du réseau
        const nodesData = [
            {nodes_data}
        ];

        const edgesData = [
            {edges_data}
        ];

        // Initialiser le réseau
        function initNetwork() {{
            nodes = new vis.DataSet(nodesData);
            edges = new vis.DataSet(edgesData);

            const container = document.getElementById('network');
            const data = {{
                nodes: nodes,
                edges: edges
            }};
            
            const options = {{
                physics: {{
                    enabled: true,
                    stabilization: {{
                        enabled: true,
                        iterations: 100,
                        updateInterval: 25
                    }},
                    barnesHut: {{
                        gravitationalConstant: -8000,
                        centralGravity: 0.3,
                        springLength: 120,
                        springConstant: 0.04,
                        damping: 0.09
                    }}
                }},
                nodes: {{
                    font: {{
                        size: 14,
                        color: '#333',
                        face: 'Segoe UI'
                    }},
                    borderWidth: 2,
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0,0,0,0.2)',
                        size: 10,
                        x: 2,
                        y: 2
                    }},
                    scaling: {{
                        min: 10,
                        max: 30
                    }}
                }},
                edges: {{
                    arrows: {{
                        to: {{
                            enabled: true,
                            scaleFactor: 1.2
                        }}
                    }},
                    font: {{
                        size: 12,
                        color: '#555'
                    }},
                    smooth: {{
                        type: 'continuous',
                        roundness: 0.5
                    }},
                    width: 2
                }},
                layout: {{
                    improvedLayout: true,
                    clusterThreshold: 150
                }},
                interaction: {{
                    hover: true,
                    hoverConnectedEdges: true,
                    selectConnectedEdges: false,
                    tooltipDelay: 200
                }}
            }};
            
            network = new vis.Network(container, data, options);
            
            // Cacher le loading
            document.querySelector('.loading').style.display = 'none';
            
            // Event listeners
            network.on("click", function (params) {{
                if (params.nodes.length > 0) {{
                    showNodeInfo(params.nodes[0]);
                }}
            }});
            
            network.on("hoverNode", function (params) {{
                network.canvas.body.container.style.cursor = 'pointer';
            }});
            
            network.on("blurNode", function (params) {{
                network.canvas.body.container.style.cursor = 'default';
            }});
            
            // Toast de succès
            showToast('Cartographie générée avec succès !');
        }}
        
        // Fonctions de contrôle
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{physics: {{enabled: physicsEnabled}}}});
            
            const btn = event.target.closest('.btn');
            btn.classList.toggle('active');
            
            if (physicsEnabled) {{
                btn.innerHTML = '<i class="fas fa-magic"></i> Physique';
                showToast('Physique activée');
            }} else {{
                btn.innerHTML = '<i class="fas fa-pause"></i> Statique';
                showToast('Physique désactivée');
            }}
        }}
        
        function resetView() {{
            network.fit();
            showToast('Vue centrée');
        }}
        
        function toggleIPs() {{
            showIPs = !showIPs;
            const ipNodes = nodesData.filter(node => node.group === 'ip');
            const ipNodeIds = ipNodes.map(node => node.id);
            
            if (showIPs) {{
                nodes.add(ipNodes);
                event.target.innerHTML = '<i class="fas fa-server"></i> Masquer IPs';
                showToast('IPs affichées');
            }} else {{
                nodes.remove(ipNodeIds);
                event.target.innerHTML = '<i class="fas fa-server"></i> Afficher IPs';
                showToast('IPs masquées');
            }}
        }}
        
        function exportImage() {{
            const canvas = network.canvas.frame.canvas;
            const link = document.createElement('a');
            link.download = 'cartographie_{domain}.png';
            link.href = canvas.toDataURL();
            link.click();
            showToast('Image exportée !');
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
                event.target.innerHTML = '<i class="fas fa-compress"></i> Quitter';
            }} else {{
                document.exitFullscreen();
                event.target.innerHTML = '<i class="fas fa-expand"></i> Plein écran';
            }}
        }}
        
        function showNodeInfo(nodeId) {{
            const node = nodes.get(nodeId);
            const infoPanel = document.getElementById('infoPanel');
            const nodeInfo = document.getElementById('nodeInfo');
            
            nodeInfo.innerHTML = `
                <p><strong>Nom:</strong> ${{node.label}}</p>
                <p><strong>Type:</strong> ${{node.group}}</p>
                <p><strong>Connexions:</strong> ${{network.getConnectedNodes(nodeId).length}}</p>
            `;
            
            infoPanel.style.display = 'block';
            setTimeout(() => {{
                infoPanel.style.display = 'none';
            }}, 3000);
        }}
        
        function showToast(message) {{
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 100);
            setTimeout(() => {{
                toast.classList.remove('show');
                setTimeout(() => document.body.removeChild(toast), 300);
            }}, 2000);
        }}
        
        // Initialiser au chargement
        document.addEventListener('DOMContentLoaded', initNetwork);
    </script>
</body>
</html>
        """
        
        # Préparer les données avec groupes et styles améliorés
        nodes_data = []
        node_id = 0
        node_map = {}
        
        # Compter les sous-domaines
        subdomains = [d for d in self.domains if self.root_domain in d and d != self.root_domain]
        
        # Ajouter le domaine principal
        if self.root_domain:
            nodes_data.append(f"""{{
                id: {node_id}, 
                label: '{self.root_domain}', 
                group: 'main',
                color: {{background: '#e1f5fe', border: '#01579b'}},
                size: 40,
                font: {{color: '#01579b', size: 18, face: 'Segoe UI'}}
            }}""")
            node_map[self.root_domain] = node_id
            node_id += 1
        
        # Ajouter les sous-domaines
        for domain in self.domains:
            if domain != self.root_domain:
                if self.root_domain and self.root_domain in domain:
                    # Sous-domaine
                    short_label = domain.replace(f'.{self.root_domain}', '')
                    nodes_data.append(f"""{{
                        id: {node_id}, 
                        label: '{short_label}', 
                        title: '{domain}',
                        group: 'subdomain',
                        color: {{background: '#f3e5f5', border: '#4a148c'}},
                        size: 25,
                        font: {{color: '#4a148c', size: 14}}
                    }}""")
                else:
                    # Domaine externe
                    nodes_data.append(f"""{{
                        id: {node_id}, 
                        label: '{domain[:20]}{"..." if len(domain) > 20 else ""}', 
                        title: '{domain}',
                        group: 'external',
                        color: {{background: '#fce4ec', border: '#880e4f'}},
                        size: 20,
                        font: {{color: '#880e4f', size: 12}}
                    }}""")
                
                node_map[domain] = node_id
                node_id += 1
        
        # Ajouter les IPs
        for ip in self.ips:
            label = ip[:15] + '...' if len(ip) > 15 else ip
            nodes_data.append(f"""{{
                id: {node_id}, 
                label: '{label}', 
                title: '{ip}',
                group: 'ip',
                color: {{background: '#fff3e0', border: '#e65100'}},
                size: 15,
                shape: 'diamond',
                font: {{color: '#e65100', size: 10}}
            }}""")
            node_map[ip] = node_id
            node_id += 1
        
        # Préparer les relations importantes seulement
        edges_data = []
        important_relations = ['node', 'a_record', 'cname_record', 'mx_record']
        
        for source, relation, target in self.relations:
            if relation not in important_relations:
                continue
                
            if source in node_map and target in node_map:
                color_map = {
                    'node': '#2196f3',
                    'a_record': '#4caf50',
                    'cname_record': '#ff9800',
                    'mx_record': '#f44336'
                }
                
                color = color_map.get(relation, '#666666')
                label = relation.replace('_record', '')
                
                edges_data.append(f"""{{
                    from: {node_map[source]}, 
                    to: {node_map[target]}, 
                    label: '{label}',
                    color: '{color}',
                    width: 2,
                    smooth: {{type: 'continuous'}}
                }}""")
        
        # Générer le HTML final
        html_content = html_template.format(
            domain=self.root_domain,
            domain_count=len(self.domains),
            subdomain_count=len(subdomains),
            ip_count=len(self.ips),
            relation_count=len([r for r in self.relations if r[1] in important_relations]),
            nodes_data=',\n            '.join(nodes_data),
            edges_data=',\n            '.join(edges_data)
        )
        
        output_file = f"domain_map_{self.root_domain.replace('.', '_')}.html"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Cartographie interactive générée: {output_file}")
            print(f"   🎨 Interface moderne avec contrôles interactifs")
            print(f"   📱 Design responsive pour mobile et desktop")
            print(f"   🎯 Cliquez sur les nœuds pour plus d'informations")
        except Exception as e:
            print(f"❌ Erreur lors de la génération HTML: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 domain_mapper.py <fichier_amass.txt> [options]")
        print("\nOptions:")
        print("  --graphviz         Générer avec Graphviz (défaut)")
        print("  --html             Générer une carte interactive HTML")
        print("  --text             Affichage textuel simple")
        print("  --no-ips           Masquer les adresses IP")
        print("  --show-orgs        Afficher les organisations")
        print("  --format FORMAT    Format de sortie (svg, png, pdf)")
        print("\nExemples:")
        print("  python3 domain_mapper.py subdomains.txt")
        print("  python3 domain_mapper.py subdomains.txt --html")
        print("  python3 domain_mapper.py subdomains.txt --text")
        print("  python3 domain_mapper.py subdomains.txt --format png")
        print("  python3 domain_mapper.py subdomains.txt --no-ips")
        sys.exit(1)
    
    filepath = sys.argv[1]
    mapper = DomainMapper(filepath)
    mapper.parse_amass_file()
    
    if len(mapper.domains) == 0:
        print("⚠️  Aucun domaine trouvé dans le fichier")
        sys.exit(0)
    
    # Options
    show_ips = "--no-ips" not in sys.argv
    show_orgs = "--show-orgs" in sys.argv
    output_format = "svg"
    
    if "--format" in sys.argv:
        try:
            format_index = sys.argv.index("--format") + 1
            if format_index < len(sys.argv):
                output_format = sys.argv[format_index]
        except (IndexError, ValueError):
            pass
    
    # Générer les cartes
    if "--text" in sys.argv:
        mapper.create_simple_text_map()
    elif "--html" in sys.argv:
        mapper.create_html_map()
    else:
        mapper.create_graphviz_map(output_format, show_ips, show_orgs)

if __name__ == "__main__":
    main()