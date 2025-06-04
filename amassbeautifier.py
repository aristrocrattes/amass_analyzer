#!/usr/bin/env python3
"""
Amass Beautifier - Extrait TOUS les domaines/sous-domaines d'un scan Amass
Usage: python3 amassbeautifier.py <fichier_amass.txt>
"""

import sys
import re
from typing import Set, Dict, List
from collections import defaultdict

class AmassBeautifier:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.all_domains: Set[str] = set()
        self.domain_ips: Dict[str, List[str]] = {}
        self.domain_relations: Dict[str, List[str]] = defaultdict(list)
        self.root_domain = ""
        
    def parse_amass_file(self):
        """Parse le fichier Amass et extrait TOUS les domaines/sous-domaines"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Pattern général pour extraire tous les FQDN
                    # Format: SOURCE (TYPE) --> RELATION --> TARGET (TYPE)
                    pattern = r'^(.+?) \((.+?)\) --> (.+?) --> (.+?) \((.+?)\)$'
                    match = re.match(pattern, line)
                    
                    if match:
                        source, source_type, relation, target, target_type = match.groups()
                        source = source.strip()
                        target = target.strip()
                        relation = relation.strip()
                        
                        # Collecter tous les FQDN (domaines et sous-domaines)
                        if source_type == 'FQDN':
                            self.all_domains.add(source)
                            if not self.root_domain or len(source) < len(self.root_domain):
                                # Trouver le domaine racine (le plus court)
                                if '.' in source and not source.startswith('www.'):
                                    self.root_domain = source
                        
                        if target_type == 'FQDN':
                            self.all_domains.add(target)
                        
                        # Collecter les résolutions IP
                        if relation in ['a_record', 'aaaa_record'] and target_type == 'IPAddress':
                            if source not in self.domain_ips:
                                self.domain_ips[source] = []
                            self.domain_ips[source].append(target)
                        
                        # Collecter les relations pour analyse
                        self.domain_relations[source].append(f"{relation} → {target}")
                        
        except FileNotFoundError:
            print(f"❌ Erreur: Fichier '{self.filepath}' non trouvé")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier: {e}")
            sys.exit(1)
    
    def categorize_domains(self) -> Dict[str, List[str]]:
        """Catégorise tous les domaines par type/fonction"""
        categories = {
            'Domaine Principal': [],
            'Web Services': [],
            'API & Applications': [],
            'Mail & Communication': [],
            'Admin & Management': [],
            'Development & Testing': [],
            'Infrastructure': [],
            'Externes/Tiers': [],
            'Autres': []
        }
        
        # Mots-clés pour la catégorisation
        web_keywords = ['www', 'web', 'site', 'portal', 'portail', 'app', 'application']
        api_keywords = ['api', 'rest', 'graphql', 'service', 'microservice', 'backend', 'back']
        mail_keywords = ['mail', 'webmail', 'smtp', 'pop', 'imap', 'mx', 'mta']
        admin_keywords = ['admin', 'manage', 'control', 'panel', 'dashboard', 'semafore', 'collaboration']
        dev_keywords = ['dev', 'test', 'stage', 'staging', 'demo', 'beta', 'preprod', 'sandbox']
        infra_keywords = ['ns', 'dns', 'ftp', 'sftp', 'ssh', 'vpn', 'proxy', 'cdn']
        
        for domain in sorted(self.all_domains):
            domain_lower = domain.lower()
            
            # Domaine principal (racine)
            if domain == self.root_domain:
                categories['Domaine Principal'].append(domain)
                continue
            
            # Domaines externes (pas des sous-domaines du domaine principal)
            if self.root_domain and self.root_domain not in domain:
                categories['Externes/Tiers'].append(domain)
                continue
            
            # Catégorisation par mots-clés
            categorized = False
            
            for keyword in web_keywords:
                if keyword in domain_lower:
                    categories['Web Services'].append(domain)
                    categorized = True
                    break
            
            if not categorized:
                for keyword in api_keywords:
                    if keyword in domain_lower:
                        categories['API & Applications'].append(domain)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in mail_keywords:
                    if keyword in domain_lower:
                        categories['Mail & Communication'].append(domain)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in admin_keywords:
                    if keyword in domain_lower:
                        categories['Admin & Management'].append(domain)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in dev_keywords:
                    if keyword in domain_lower:
                        categories['Development & Testing'].append(domain)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in infra_keywords:
                    if keyword in domain_lower:
                        categories['Infrastructure'].append(domain)
                        categorized = True
                        break
            
            if not categorized:
                categories['Autres'].append(domain)
        
        return categories
    
    def display_simple_list(self):
        """Affiche la liste complète des domaines"""
        print(f"\n🎯 Tous les domaines découverts (scan de {self.root_domain})")
        print("=" * 70)
        
        for i, domain in enumerate(sorted(self.all_domains), 1):
            ip_info = ""
            if domain in self.domain_ips:
                ips = self.domain_ips[domain]
                ip_info = f" → {', '.join(ips[:2])}" + ("..." if len(ips) > 2 else "")
            
            # Marquer le domaine principal
            marker = " 🏠" if domain == self.root_domain else ""
            external = " 🌐" if self.root_domain and self.root_domain not in domain else ""
            
            print(f"{i:2d}. {domain}{ip_info}{marker}{external}")
        
        print(f"\n📊 Total: {len(self.all_domains)} domaines découverts")
        print(f"🏠 = Domaine principal | 🌐 = Domaine externe")
    
    def display_categorized(self):
        """Affiche les domaines catégorisés"""
        categories = self.categorize_domains()
        
        print(f"\n🎯 Analyse complète des domaines (scan de {self.root_domain})")
        print("=" * 80)
        
        total_displayed = 0
        for category, domains in categories.items():
            if domains:
                print(f"\n📂 {category} ({len(domains)})")
                print("-" * 40)
                for domain in domains:
                    ip_info = ""
                    if domain in self.domain_ips:
                        ips = self.domain_ips[domain]
                        ip_info = f" → {ips[0]}" + (f" (+{len(ips)-1})" if len(ips) > 1 else "")
                    
                    print(f"  ├── {domain}{ip_info}")
                    total_displayed += 1
        
        print(f"\n📊 Résumé: {total_displayed} domaines au total")
    
    def display_with_details(self):
        """Affiche les domaines avec leurs relations détaillées"""
        print(f"\n🎯 Analyse détaillée des domaines (scan de {self.root_domain})")
        print("=" * 80)
        
        for domain in sorted(self.all_domains):
            print(f"\n🔍 {domain}")
            
            # Afficher les IPs
            if domain in self.domain_ips:
                for ip in self.domain_ips[domain]:
                    print(f"  └── 📍 {ip}")
            
            # Afficher les relations
            if domain in self.domain_relations:
                for relation in self.domain_relations[domain][:3]:  # Limiter à 3
                    print(f"  └── 🔗 {relation}")
                if len(self.domain_relations[domain]) > 3:
                    print(f"  └── ... et {len(self.domain_relations[domain]) - 3} autres")
    
    def export_to_file(self, output_file: str, format_type: str = "simple"):
        """Exporte tous les domaines vers un fichier"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format_type == "simple":
                    for domain in sorted(self.all_domains):
                        f.write(f"{domain}\n")
                
                elif format_type == "with_ips":
                    for domain in sorted(self.all_domains):
                        if domain in self.domain_ips:
                            ips = ", ".join(self.domain_ips[domain])
                            f.write(f"{domain} → {ips}\n")
                        else:
                            f.write(f"{domain}\n")
                
                elif format_type == "categorized":
                    categories = self.categorize_domains()
                    for category, domains in categories.items():
                        if domains:
                            f.write(f"\n[{category}]\n")
                            for domain in domains:
                                f.write(f"{domain}\n")
            
            print(f"✅ {len(self.all_domains)} domaines exportés vers: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
    
    def export_clean_domains(self, output_file: str):
        """Exporte uniquement les noms de domaines, un par ligne, sans aucune information supplémentaire"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for domain in sorted(self.all_domains):
                    f.write(f"{domain}\n")
            
            print(f"✅ {len(self.all_domains)} domaines exportés (format clean) vers: {output_file}")
            print(f"📝 Format: un domaine par ligne, sans IPs ni autres informations")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export clean: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 amassbeautifier.py <fichier_amass.txt> [options]")
        print("\nOptions:")
        print("  --simple        Affichage simple (défaut)")
        print("  --categorized   Affichage catégorisé")
        print("  --detailed      Affichage avec détails des relations")
        print("  --export FILE   Exporter vers un fichier")
        print("  --export-ips    Inclure les IPs dans l'export")
        print("  --export-clean FILE  Exporter uniquement les noms de domaines")
        print("\nExemples:")
        print("  python3 amassbeautifier.py subdomains.txt")
        print("  python3 amassbeautifier.py subdomains.txt --categorized")
        print("  python3 amassbeautifier.py subdomains.txt --detailed")
        print("  python3 amassbeautifier.py subdomains.txt --export all_domains.txt")
        print("  python3 amassbeautifier.py subdomains.txt --export-clean clean_domains.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    beautifier = AmassBeautifier(filepath)
    beautifier.parse_amass_file()
    
    if len(beautifier.all_domains) == 0:
        print("⚠️  Aucun domaine trouvé dans le fichier")
        sys.exit(0)
    
    # Options d'affichage
    if "--detailed" in sys.argv:
        beautifier.display_with_details()
    elif "--categorized" in sys.argv:
        beautifier.display_categorized()
    else:
        beautifier.display_simple_list()
    
    # Export si demandé
    if "--export" in sys.argv:
        try:
            export_index = sys.argv.index("--export") + 1
            if export_index < len(sys.argv):
                export_file = sys.argv[export_index]
                if "--export-ips" in sys.argv:
                    beautifier.export_to_file(export_file, "with_ips")
                else:
                    beautifier.export_to_file(export_file, "simple")
        except (IndexError, ValueError):
            print("❌ Erreur: Spécifiez un nom de fichier après --export")
    
    # Export clean si demandé
    if "--export-clean" in sys.argv:
        try:
            export_index = sys.argv.index("--export-clean") + 1
            if export_index < len(sys.argv):
                export_file = sys.argv[export_index]
                beautifier.export_clean_domains(export_file)
        except (IndexError, ValueError):
            print("❌ Erreur: Spécifiez un nom de fichier après --export-clean")

if __name__ == "__main__":
    main()