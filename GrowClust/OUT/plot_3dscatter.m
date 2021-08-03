%plot location distribution in 3d
clc; clear all; close all;
loc3 = './out.growclust_cat'

a = load(loc3);
lat = a(:,8);
lon = a(:,9);
dep = a(:,10);

scatter3(lon,lat,dep,'filled','b'), view(-60,60);
%ylim([42.5,43.0]) %lat range
%xlim([12.9,13.4]) %lon range
%zlim([0,20]);   %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',20)
title('Growclust catalog');
%saveas(gcf,'3Dlocation.jpg')
