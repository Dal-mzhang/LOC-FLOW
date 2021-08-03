%plot location distribution in 3d
loc = 'new.cat'

a = load(loc);
lat = a(:,5);
lon = a(:,6);
dep = a(:,7);

scatter3(lon,lat,dep,'filled','b'), view(-60,60);
ylim([42.5,43.0])
xlim([12.9,13.4])
zlim([0,20]);
grid on; alpha(0.45); box on;

set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth (km)');
set(gca,'FontSize',20)
saveas(gcf,'3dlocation.pdf')

