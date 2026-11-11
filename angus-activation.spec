Name:		angus-activation
Version:	2.0.3
Release:	1
Summary:	Jakarta Activation registry implementation
Group:		Development/Java
License:	BSD-3-Clause
URL:		https://github.com/eclipse-ee4j/angus-activation
Source0:	https://github.com/eclipse-ee4j/angus-activation/archive/refs/tags/%{version}.tar.gz#/angus-activation-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(jakarta.activation:jakarta.activation-api)

%description
Angus Activation %{version} implements the Jakarta Activation mailcap and
MIME type registries. JAXB 4.0.9 loads these registries at runtime.

%prep
%autosetup -n angus-activation-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
find activation-registry/src/main/java -name '*.java' \
	! -name 'module-info.java' \
	! -name 'AngusActivationFeature.java' > sources.list
test "$(wc -l < sources.list)" -eq 7
mkdir -p classes
javac --release 8 -encoding UTF-8 \
	-cp %{_javadir}/jakarta.activation-api.jar \
	-d classes @sources.list
mkdir -p classes/META-INF/services
/bin/cp -a activation-registry/src/main/resources/META-INF/services/. classes/META-INF/services/
jar cf angus-activation.jar -C classes .
jar tf angus-activation.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp angus-activation.jar org.eclipse.angus.activation.MailcapRegistryProviderImpl | grep -F 'major version: 52'

cat > angus-activation.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.eclipse.angus</groupId>
  <artifactId>angus-activation</artifactId>
  <version>2.0.3</version>
  <name>Angus Activation Registries</name>
  <description>Jakarta Activation mailcap and MIME type registries</description>
  <licenses>
    <license>
      <name>BSD-3-Clause</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>jakarta.activation</groupId>
      <artifactId>jakarta.activation-api</artifactId>
      <version>2.1.3</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact angus-activation.pom:angus-activation.jar \
	--file-name angus-activation \
	--filelist .mfiles

%check
mkdir -p check
cat > check/Smoke.java << 'END'
import jakarta.activation.MailcapRegistry;
import org.eclipse.angus.activation.MailcapRegistryProviderImpl;
public class Smoke {
	public static void main(String[] args) throws Exception {
		MailcapRegistry registry = new MailcapRegistryProviderImpl().getInMemory();
		registry.appendToMailcap("text/plain; angus.Handler");
		String found = "";
		for (String type : registry.getMimeTypes()) {
			if ("text/plain".equals(type)) {
				found = type;
			}
		}
		if (found.isEmpty()) {
			throw new AssertionError("no text/plain");
		}
		System.out.println("angus_ok " + found);
	}
}
END
JAR=%{buildroot}%{_javadir}/angus-activation.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 \
	-cp "$JAR:%{_javadir}/jakarta.activation-api.jar" \
	-d check check/Smoke.java
java -cp "check:$JAR:%{_javadir}/jakarta.activation-api.jar" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'angus_ok text/plain' check/out.txt

%files -f .mfiles
%doc LICENSE.md NOTICE.md
