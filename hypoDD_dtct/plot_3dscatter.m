res = 'hypoDD.reloc'

a = load(res);

lat = a(:,2);
lon = a(:,3);
dep = a(:,4);
res = a(:,23);

scatter3(lon,lat,dep,'filled','b'), view(-60,60);
%ylim([42.5,43.0])
%xlim([12.9,13.4])
%zlim([0,20]);
grid on; alpha(0.45); box on;

set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth (km)');
set(gca,'FontSize',20)
%saveas(gcf,'3dlocation.pdf')
